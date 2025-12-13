from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.user import UserRegister, User, UserPublic
from app.core.security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])

@router.post(
    "/register", 
    status_code=status.HTTP_201_CREATED,
    response_model=UserPublic
)
def create_user(
    user: UserRegister,
    session: Session = Depends(get_db)
    ):
    username_record = session.exec(
        select(User).where(User.username == user.username)
    ).first()
    if username_record is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
    
    email_record = session.exec(
        select(User).where(User.email == user.email)
    ).first()
    if email_record is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    
    new_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hash_password(user.password)
        )
    
    try:
        session.add(new_user)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
        
    session.refresh(new_user)
    return UserPublic(id=new_user.id, username=new_user.username)