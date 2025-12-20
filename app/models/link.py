from enum import Enum
from sqlmodel import SQLModel, Field

from app.models.member import AccessLevel


class RepositoryKeyword(SQLModel, table=True):
    __tablename__ = "repository_keywords"
    
    repository_id: int = Field(
        default=None, foreign_key="repositories.id", primary_key=True
    )
    keyword_id: int = Field(
        default=None, foreign_key="keywords.id", primary_key=True
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