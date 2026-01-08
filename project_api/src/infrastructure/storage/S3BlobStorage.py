import aioboto3
from botocore.exceptions import ClientError
from src.application.abstraction.IFileStorage import IBlobStorage

class S3BlobStorage(IBlobStorage):
    def __init__(self, bucket: str, region: str, aws_access_key_id: str, aws_secret_access_key: str):
        self.bucket = bucket
        self.region = region
        self._session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )

    def _client(self):
        return self._session.client("s3")

    async def save(self, file_stream, file_hash: str) -> str:
        async with self._client() as s3:
            content = await file_stream.read()
            await s3.put_object(Bucket=self.bucket, Key=file_hash, Body=content)
        return file_hash

    async def get(self, file_hash: str):
        async with self._client() as s3:
            obj = await s3.get_object(Bucket=self.bucket, Key=file_hash)
            body = obj["Body"]  #

            async for chunk in body.iter_chunks(chunk_size=1024 * 64):
                if chunk:  
                    yield chunk

    async def delete(self, file_hash: str) -> None:
        async with self._client() as s3:
            await s3.delete_object(Bucket=self.bucket, Key=file_hash)

    async def exists(self, file_hash: str) -> bool:
        async with self._client() as s3:
            try:
                await s3.head_object(Bucket=self.bucket, Key=file_hash)
                return True
            except ClientError as e:
                code = e.response["Error"].get("Code")
                if code in ("404", "NoSuchKey", "NotFound"):
                    return False
                raise
