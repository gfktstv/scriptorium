from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.repository import Repository
from app.models.member import MemberPublic, MemberUpdate
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
async def update_membership(
    repository_id: int,
    user_id: int,
    membership_data: MemberUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    repository = await session.get(Repository, repository_id)
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
        
    target_user = await session.get(User, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    membership = (await session.exec(
        select(RepositoryAccess).where(
                (RepositoryAccess.repository_id == repository_id)
                & (RepositoryAccess.user_id == user_id)
        )
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
    await session.commit()
    
    return {"message": "Membership updated successfully"}

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=List[MemberPublic]
)
async def get_list_of_members(
    repository_id: int,
    session: AsyncSession = Depends(get_db)
):
    statement = select(RepositoryAccess).where(
        (RepositoryAccess.repository_id == repository_id)
    )
    statement = statement.options(selectinload(RepositoryAccess.user))
    
    members = (await session.exec(statement)).all()
    
    return members

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_member(
    repository_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    if repository.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete members of this repository"
        )
        
    await session.exec(
        delete(RepositoryAccess).where(
            (RepositoryAccess.repository_id == repository_id)
            & (RepositoryAccess.user_id == user_id)
        )
    )

    await session.commit()
    return None