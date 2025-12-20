from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select

from app.db.session import get_db
from app.models.user import User
from app.models.repository import Repository
from app.models.member import MemberUpdate
from app.models.link import RepositoryAccess
from app.core.security import get_current_user


router = APIRouter(
    prefix="/repositories/{repository_id}/members", 
    tags=["Members"]
)

@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
)
def update_membership(
    repository_id: int,
    user_id: int,
    membership_data: MemberUpdate,
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
            detail="You are not authorized to update members access of this repository"
        )
        
    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    membership = session.exec(select(RepositoryAccess).where(
        (RepositoryAccess.repository_id == repository_id)
        & (RepositoryAccess.user_id == user_id)
    )).first()
    if membership is not None:
        membership.access = membership_data.access
    else:
        membership = RepositoryAccess(
            repository_id=repository_id,
            user_id=user_id,
            access=membership_data.access
        )
        
    session.add(membership)
    session.commit()
    
    return {"message": "Membership updated successfully"}