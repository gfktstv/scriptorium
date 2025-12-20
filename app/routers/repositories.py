from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import UserPublic, User
from app.models.repository import RepositoryUpdate, RepositoryPublic, RepositoryCreate, Repository
from app.models.keyword import Keyword
from app.core.security import get_current_user, get_current_user_optional


router = APIRouter(prefix="/repositories", tags=["Repositories"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=RepositoryPublic
)
def create_repository(
    repository: RepositoryCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    db_keywords = []
    if repository.keywords:
        unique_keywords = set(k.lower().strip() for k in repository.keywords)
        for keyword in unique_keywords:
            existing_keyword = session.exec(
                select(Keyword).where(Keyword.name == keyword)
            ).first()
            if existing_keyword is not None:
                db_keywords.append(existing_keyword)
            else:
                db_keywords.append(Keyword(name=keyword))
    
    record = session.exec(
        select(Repository).where(
            (Repository.owner_id == current_user.id)
            & (Repository.name == repository.name)
        )
    ).first()
    if record is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Repository with this name already exists"
        )
    
    new_repository = Repository(
        name=repository.name,
        owner_id=current_user.id,
        is_public=repository.is_public,
        description=repository.description,
        keywords=db_keywords
    )
    
    try:
        session.add(new_repository)
        session.commit()
        session.refresh(new_repository)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository already exists"
        )
        
    return RepositoryPublic(
        name=new_repository.name, 
        is_public=new_repository.is_public,
        description=new_repository.description,
        id=new_repository.id,
        owner=UserPublic(id=current_user.id, username=current_user.username),
        keywords=db_keywords
        )
        
@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=List[RepositoryPublic]
)
def search_repositories(
    repository_name: Optional[str] = None,
    keywords: Optional[str] = None,
    owner_username: Optional[str] = None,
    offset: int = 0,
    limit: int = Query(default=20, le=100),
    session: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user_optional)
):
    statement = select(Repository)
    if current_user is not None:
        statement = statement.where(
            (Repository.is_public == True) 
            | (Repository.owner_id == current_user.id)
        )
    else:
        statement = statement.where((Repository.is_public == True))
    
    if owner_username:
        normalized_owner_username = owner_username.lower().strip()
        statement = statement.join(User).where(
            User.username.ilike(f"%{normalized_owner_username}%")
            )
    
    if repository_name:
        normalized_repository_name = repository_name.lower().strip()
        statement = statement.where(
            Repository.name.ilike(f"%{normalized_repository_name}%")
            )
        
    if keywords:
        keyword_list = [k.lower().strip() for k in keywords.split(",") if k.strip()]
        if keyword_list:
            statement = statement.where(
                Repository.keywords.any(Keyword.name.in_(keyword_list))
            )
    
    # To fetch owners (User) at the same time as the repos     
    statement = statement.offset(offset).limit(limit).options(
        selectinload(Repository.owner)
        )
            
    repositories = session.exec(statement).all()
    return repositories

@router.get(
    "/{username}/{repository_name}",
    status_code=status.HTTP_200_OK,
    response_model=RepositoryPublic
)
def get_repository(
    username: str,
    repository_name: str,
    session: Session = Depends(get_db)
):
    normalized_username = username.lower().strip()
    normalized_repository_name = repository_name.lower().strip()
    
    statement = select(Repository)
    statement = statement.join(User).where(
        User.username.ilike(normalized_username)
    )
    statement = statement.where(
        Repository.name.ilike(normalized_repository_name)
    )
    statement = statement.options(
        selectinload(Repository.owner), 
        selectinload(Repository.keywords)
    )
    
    repository = session.exec(statement).first()
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository or User not found"
        )
    
    return repository

@router.get(
    "/{repository_id}",
    status_code=status.HTTP_200_OK,
    response_model=RepositoryPublic
)
def get_repository_by_id(
    repository_id: int,
    session: Session = Depends(get_db)
):
    statement = select(Repository).where(Repository.id == repository_id)
    statement = statement.options(selectinload(Repository.owner))
    statement = statement.options(selectinload(Repository.keywords))
    repository = session.exec(statement).first()
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    return repository

@router.patch(
    "/{repository_id}",
    status_code=status.HTTP_200_OK,
    response_model=RepositoryPublic
)
def update_repository(
    repository_id: int,
    repository_update: RepositoryUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    repository = session.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    if repository.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this repository"
        )
        
    # Keywords are processed separately, therefore we pop keywords field
    # from update_date, because after that we apply sqlmodel_update
    # for simple fields like name, description and is_public
    update_data = repository_update.model_dump(exclude_unset=True)
    if "keywords" in update_data:
        keywords = update_data.pop("keywords")
        if keywords:
            normalised_keywords = set(
                k.lower().strip() for k in keywords
            )
            
            new_db_keywords = []
            for keyword in normalised_keywords:
                existing_keyword = session.exec(select(Keyword).where(Keyword.name == keyword)).first()
                if existing_keyword is not None:
                    new_db_keywords.append(existing_keyword)
                else:
                    new_db_keywords.append(Keyword(name=keyword))
                    
        repository.keywords = new_db_keywords
        
    repository.sqlmodel_update(update_data)
    
    session.add(repository)
    session.commit()
    session.refresh(repository)
    
    # We already fetched current user and assured that 
    # this user is the owner. To avoid owner fetch we simply set owner
    # as current_user (optimization)
    if not repository.owner:
        repository.owner = current_user
        
    return repository