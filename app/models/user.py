import re
from typing import Optional

from sqlmodel import SQLModel, Field
from pydantic import EmailStr, field_validator


class UserPublic(SQLModel):
    id: int
    username: str
    
class UserLogin(SQLModel):
    username: str = Field(description="Username or email")
    password: str

class UserBase(SQLModel):
    username: str = Field(
        min_length=3, 
        max_length=30, 
        schema_extra={"pattern": r"^[a-zA-Z0-9_]{3,30}$"},
        description="Username must be 3-30 characters long and can only contain letters, numbers, and underscores.",
        unique=True
    )
    email: EmailStr = Field(unique=True, index=True)
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_]+", v):
            raise ValueError(
                "Username can only contain Latin letters, numbers, and underscores"
            )
        return v
    
class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

class UserRegister(UserBase):
    password: str = Field(
        min_length=8, 
        max_length=72,
        schema_extra={"pattern": r"^[a-zA-Z0-9_]{8,72}$"},
        description="Password must be 8-72 characters long, include at least one uppercase letter, one lowercase letter, one number."
    )
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_!@#$%^&*()\-+]+", v):
            raise ValueError(
                "Password can only contain Latin letters, numbers, and special characters like _!@#$%^&*()-+"
            )
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must include at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must include at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must include at least one number.")
        return v