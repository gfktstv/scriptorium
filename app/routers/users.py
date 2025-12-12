from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select

from app.db.session import get_db
from app.models.user import UserRegister, User
from app.core.security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])

@router.post(
    "/register", 
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user: UserRegister,
    session: Session = Depends(get_db)
    ):
    record = session.exec(
        select(User).where(
            (User.username == user.username) | 
            (User.email == user.email)
        )
    ).first()
    if record is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    
    session.add(new_user)
    session.commit()