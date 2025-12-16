import re
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from pydantic import field_validator

from app.models.keyword import Keyword
from app.models.link import RepositoryKeywordLink

    
class RepositoryBase(SQLModel):
    name: str = Field(
        min_length=3,
        max_length=30,
        schema_extra={"pattern": r"^[a-zA-Z0-9_]{3,30}$"},
        description="Repository name must be 3-30 characters long and can only contain letters, numbers, and underscores.",
        index=True
    )
    is_public: bool = False
    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        schema_extra={"pattern": r".{1,256}$"},
        description="Short description of the repository."
    )

class RepositoryCreate(RepositoryBase):
    keywords: List[str] = []
    
class RepositoryPublic(RepositoryBase):
    id: int
    owner_id: int
    keywords: List[str] = []

class Repository(RepositoryBase, table=True):
    __tablename__ = "repositories"
    
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="unique_owner_repo_name"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(unique=True, foreign_key="users.id", index=True)
    
    # This field does not exist in SQL — it is simply
    # a smart way to save keywords for each repository
    # saving lines of code.
    keywords: List["Keyword"] = Relationship(
        back_populates="repositories", 
        link_model=RepositoryKeywordLink
    )
    
    @field_validator("name")
    @classmethod
    def validate_rep_name(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_]+", v):
            raise ValueError(
                "Repository name can only contain Latin letters, numbers, and underscores"
            )
        return v