from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/users/token", auto_error=False
    )
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str | int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"sub": str(subject), "exp": expire}
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await session.get(User, int(user_id))
    if user is None:
        raise credentials_exception
        
    return user

# This function is needed to show public objects and private if 
# a user is authorized. For example, to search repos 
# (if authorized will also show repos owned by the user).
async def get_current_user_optional(
    token: Annotated[str, Depends(oauth2_scheme_optional)],
    session: Annotated[AsyncSession, Depends(get_db)]
) -> Optional[User]:
    if token is None:
        return None
    
    try:
        user = await get_current_user(token, session)
        return user
    except HTTPException:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)