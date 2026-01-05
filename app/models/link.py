from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from app.models.member import AccessLevel
from app.models.user import User


class RepositoryKeyword(SQLModel, table=True):
    __tablename__ = "repository_keywords"
    
    repository_id: int = Field(
        default=None, 
        foreign_key="repositories.id", 
        primary_key=True,
        ondelete="CASCADE"
    )
    keyword_id: int = Field(
        default=None, 
        foreign_key="keywords.id", 
        primary_key=True,
        ondelete="CASCADE"
    )
    
class RepositoryAccess(SQLModel, table=True):
    __tablename__ = "repository_access"
    
    repository_id: int = Field(
        default=None, 
        foreign_key="repositories.id", 
        primary_key=True,
        ondelete="CASCADE"
    )
    user_id: int = Field(
        default=None, 
        foreign_key="users.id", 
        primary_key=True,
        ondelete="CASCADE"
    )
    access: AccessLevel = Field(
        default=AccessLevel.VIEW
    )
    
    user: Optional["User"] = Relationship()