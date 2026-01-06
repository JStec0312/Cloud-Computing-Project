import aioboto3
from src.infrastructure.db import session
from src.application.abstraction.IFileStorage import IBlobStorage

class S3BlobStorage(IBlobStorage):
    def __init__(self, bucket: str, region: str | None = None):
        self.bucket = bucket
        self.region = region


    async def save(self, file_stream, file_hash):
        session = aioboto3.Session()
        async with session.client(
        "s3",
        region_name=self.region
    ) as s3:
            content = await file_stream.read()   # <-- KLUCZ
            await s3.put_object(
                Bucket=self.bucket,
                Key=file_hash,
                Body=content
            )
        return file_hash

    async def get(self, file_hash):
        session = aioboto3.Session()
        async with session.client("s3", region_name=self.region) as s3:
            obj = await s3.get_object(
                Bucket=self.bucket,
                Key=file_hash
            )
            async with obj["Body"] as stream:
                while chunk := await stream.read(1024 * 64):
                    yield chunk

    async def delete(self, file_hash):
        session = aioboto3.Session()
        async with session.client("s3", region_name=self.region) as s3:
            await s3.delete_object(
                Bucket=self.bucket,
                Key=file_hash
            )

    async def exists(self, file_hash):
        session = aioboto3.Session()
        async with session.client("s3", region_name=self.region) as s3:
            try:
                await s3.head_object(
                    Bucket=self.bucket,
                    Key=file_hash
                )
                return True
            except Exception:
                return False
