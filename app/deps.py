import mimetypes
from functools import lru_cache

# TODO: add libmagic dependency in readme and installation instructions
import magic
from fastapi import Depends, HTTPException, status, UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_current_user_optional
from app.core.constants import FILE_UPLOAD_CONSTRAINTS
from app.db.session import get_db
from app.models import User
from app.models.link import RepositoryAccess
from app.models.repository import Repository
from app.models.member import AccessLevel
from app.s3.s3_client import S3Client
from app.core.config import settings


async def get_readable_repository(
        repository_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: User | None = Depends(get_current_user_optional)
) -> Repository:
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    if repository.is_public:
        return repository

    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated to view private repository")

    if repository.owner_id == current_user.id:
        return repository

    membership = (await session.exec(
        select(RepositoryAccess).where(
            (RepositoryAccess.repository_id == repository_id)
            & (RepositoryAccess.user_id == current_user.id)
        )
    )).first()
    if membership is not None:
        return repository

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not authorized")

async def get_editable_repository(
        repository_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user_optional)
) -> Repository:
    repository = await session.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated to edit private repository")

    if repository.owner_id == current_user.id:
        return repository

    membership = (await session.exec(
        select(RepositoryAccess).where(
            (RepositoryAccess.repository_id == repository_id)
            & (RepositoryAccess.user_id == current_user.id)
        )
    )).first()
    if membership is not None and membership.access == AccessLevel.EDIT:
        return repository

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not authorized to edit private repository")

async def validate_file_upload(file: UploadFile) -> int:
    """
    Validate the uploaded file's type and size. 
    HTTPException is raised if invalid.
    Returns actual size if valid. 
    """
    # Quick check based on content_type
    mime_type, _ = mimetypes.guess_type(file.filename)
    if mime_type not in FILE_UPLOAD_CONSTRAINTS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}"
        )
        
    max_size = FILE_UPLOAD_CONSTRAINTS[mime_type]
    file_content = await file.read(max_size + 1)
    
    # Check MIME type using python-magic (more thorough)
    if magic.from_buffer(file_content, mime=True) not in FILE_UPLOAD_CONSTRAINTS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    actual_size = len(file_content)
    if actual_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File size exceeds the maximum allowed size of {max_size / 1024 / 1024} megabytes for type {mime_type}"
        )
        
    return actual_size, file_content

@lru_cache()
def get_s3_client() -> S3Client:
    return S3Client(
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        endpoint_url=settings.S3_ENDPOINT_URL,
        bucket_name=settings.S3_BUCKET_NAME
    )