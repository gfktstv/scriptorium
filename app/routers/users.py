from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password, create_access_token
from app.db.session import get_db
from app.models.user import UserPublic, User, UserRegister, UserLogin
from app.models.token import Token


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
    normalized_username = user.username.lower().strip()
    normalized_email = user.email.lower().strip()
    
    username_record = session.exec(
        select(User).where(User.username == normalized_username)
    ).first()
    if username_record is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
    
    email_record = session.exec(
        select(User).where(User.email == normalized_email)
    ).first()
    if email_record is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    
    new_user = User(
            username=normalized_username,
            email=normalized_email,
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

def authenticate_user(session: Session, identifier: str, password: str):
    credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User with this email/username does not exist or password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    identifier = identifier.lower().strip()
    user = session.exec(
        select(User).where(
            (User.username == identifier)
            | (User.email == identifier)
        )
    ).first()
    
    if user is None or not verify_password(password, user.hashed_password):
        raise credentials_exception
    
    return user

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=Token
)
def login_user(
    user: UserLogin,
    session: Session = Depends(get_db)
):
    user = authenticate_user(
            session, 
            identifier=user.username, 
            password=user.password
            )
    
    return Token(access_token=create_access_token(user.id))

# Endpoint for Swagger UI (authorize button)
@router.post(
    "/token",
    response_model=Token,
    include_in_schema=False
)
def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db)
):
    user = authenticate_user(
            session, 
            identifier=form_data.username, 
            password=form_data.password
            )
    
    return Token(access_token=create_access_token(user.id))