import asyncio
from contextlib import asynccontextmanager

from aiobotocore.session import get_session
from fastapi import UploadFile


CHUNK_SIZE = 5 * 1024 * 1024

class S3Client:
    def __init__(
            self,
            access_key: str,
            secret_key: str,
            endpoint_url: str,
            bucket_name: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
        }
        self.bucket_name = bucket_name
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    # TODO: add streaming
    async def upload_file(
            self,
            file_content,
            storage_key: str
    ):        
        async with self.get_client() as client:
            await client.put_object(
                    Bucket=self.bucket_name,
                    Key=storage_key,
                    Body=file_content,     
            )

    async def delete_file(self, storage_key: str):
        async with self.get_client() as client:
            await client.delete_object(
                Bucket=self.bucket_name, 
                Key=storage_key
            )

    async def get_file(self, storage_key: str):
        async with self.get_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket_name, 
                    Key=storage_key
                )
                async for chunk in response["Body"].iter_chunks(chunk_size=CHUNK_SIZE):
                    yield chunk