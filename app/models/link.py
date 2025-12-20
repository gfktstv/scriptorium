from enum import Enum
from sqlmodel import SQLModel, Field

class RepositoryKeyword(SQLModel, table=True):
    __tablename__ = "repository_keywords"
    
    repository_id: int = Field(
        default=None, foreign_key="repositories.id", primary_key=True
    )
    keyword_id: int = Field(
        default=None, foreign_key="keywords.id", primary_key=True
    )