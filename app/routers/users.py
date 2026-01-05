from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
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
async def create_user(
    user: UserRegister,
    session: AsyncSession = Depends(get_db)
    ) -> UserPublic:
    normalized_username = user.username.lower().strip()
    normalized_email = user.email.lower().strip()
    
    username_record = (await session.exec(
        select(User).where(User.username.ilike(normalized_username))
    )).first()
    if username_record is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
    
    email_record = (await session.exec(
        select(User).where(User.email.ilike(normalized_email))
    )).first()
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
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
        
    await session.refresh(new_user)
    return UserPublic(id=new_user.id, username=new_user.username)

async def authenticate_user(
    session: AsyncSession, 
    identifier: str, 
    password: str
    ) -> User:
    credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User with this email/username does not exist or password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    identifier = identifier.lower().strip()
    user = (await session.exec(
        select(User).where(
            (User.username.ilike(identifier))
            | (User.email.ilike(identifier))
        )
    )).first()
    
    if user is None or not verify_password(password, user.hashed_password):
        raise credentials_exception
    
    return user

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=Token
)
async def login_user(
    user: UserLogin,
    session: AsyncSession = Depends(get_db)
) -> Token:
    user = await authenticate_user(
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
async def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
) -> Token:
    user = await authenticate_user(
        session, 
        identifier=form_data.username, 
        password=form_data.password
    )
    
    return Token(access_token=create_access_token(user.id))

@router.get(
    "/{username}",
    response_model=UserPublic
)
async def get_user(
    username: str,
    session: AsyncSession = Depends(get_db)
) -> UserPublic:
    normalized_username = username.lower().strip()
    user = (await session.exec(
        select(User).where(User.username.ilike(normalized_username))
    )).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    return UserPublic(id=user.id, username=user.username)