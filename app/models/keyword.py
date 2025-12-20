from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from app.models.link import RepositoryKeyword


if TYPE_CHECKING:
    # This block is only executed by Type Checkers (mypy/VSCode), 
    # NOT by Python at runtime. This prevents circular imports.
    from .repository import Repository


class Keyword(SQLModel, table=True):
    __tablename__ = "keywords"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    
    # This field does not exist in SQL — it is simply
    # a smart way to save keywords for each repository
    # saving lines of code.
    repositories: List["Repository"] = Relationship(
        back_populates="keywords", 
        link_model=RepositoryKeyword
    )