from typing import Optional, List

from sqlmodel import SQLModel, Field


class FileError(SQLModel):
    filename: str
    detail: str
    
class UploadResponse(SQLModel):
    uploaded: Optional[List["RepositoryObjectBase"]] = None
    errors: Optional[List[FileError]] = None

class RepositoryObjectBase(SQLModel):
    name: str = Field(
        min_length=1,
        max_length=256,
        schema_extra={"pattern": "^[a-zA-Z0-9_-]{1,256}$"},
        description="Folder or file name",
        index=True
    )
    # int32 is enough for .md and other text-like extensions
    size: Optional[int] = Field(
        default=0,  # For folders
        description="Size in bytes",
    )
    is_folder: Optional[bool] = None

class RepositoryObject(RepositoryObjectBase, table=True):
    __tablename__ = "objects"

    id: int = Field(primary_key=True)
    repository_id: int = Field(foreign_key="repositories.id")
    parent_id: Optional[int] = Field(
        default=None,
        foreign_key="objects.id"
    )
    storage_key: Optional[str] = Field(
        default=None,
        description="S3 UUID key",
    )