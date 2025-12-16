from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.user import User
from app.models.repository import RepositoryCreate, Repository
from app.models.keyword import Keyword
from app.core.security import get_current_user


router = APIRouter(prefix="/repositories", tags=["Repositories"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED
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
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository already exists"
        )