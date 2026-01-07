import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlmodel import Session, select
from starlette import status
from botocore.exceptions import ClientError

from app.s3.s3_client import S3Client
from app.db.session import get_db
from app.models.repository import Repository
from app.models.object import FileError, UploadResponse, RepositoryObjectBase, RepositoryObject
from app.deps import get_readable_repository, get_editable_repository, validate_file_upload, get_s3_client


router = APIRouter(prefix="/{repository_id}/objects", tags=["Objects"])

# TODO: add limit to the number of requests
# TODO: add limit to total size per request (500MB) ?
# TODO: add limits to total size of files in repository (5GB)
# TODO: add limits to total storage per user (5GB)
@router.post(
    "/files",
    status_code=status.HTTP_201_CREATED,
    response_model=UploadResponse
)
async def upload_files(
    files: List[UploadFile],
    parent_id: Optional[int] = None,
    repository: Repository = Depends(get_editable_repository),
    session: Session = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_client)
):
    uploaded = []
    errors = []
    for file in files:
        try:
            size, file_content = await validate_file_upload(file)
            storage_key = str(uuid.uuid4())
            
            await s3_client.upload_file(
                file_content=file_content,
                storage_key=storage_key
            )
            
            uploaded.append(RepositoryObject(
                name=file.filename,
                size=size,
                is_folder=False,
                repository_id=repository.id,
                parent_id=parent_id,
                storage_key=storage_key
            ))
        except (HTTPException, ClientError) as e:
            errors.append(FileError(
                filename=file.filename,
                detail=str(e)
            ))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Internal server error during file upload"
            )
            
    session.add_all(uploaded)
    await session.commit()
    
    return UploadResponse(
        uploaded=uploaded if uploaded else None,
        errors=errors if errors else None
    )

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=List[RepositoryObjectBase]
)
async def show_repository_objects(
    parent_id: Optional[int] = None,
    repository: Repository = Depends(get_readable_repository),
    session: Session = Depends(get_db)
) -> List[RepositoryObjectBase]:
    statement = select(RepositoryObject).where(
        (RepositoryObject.repository_id == repository.id)
        & (RepositoryObject.parent_id == parent_id)
    )
    
    return (await session.exec(statement)).all()