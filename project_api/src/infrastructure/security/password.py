from passlib.context import CryptContext
from fastapi.concurrency import run_in_threadpool

class PasswordHasher:
    def __init__(self):
        self._ctx = CryptContext(schemes=["argon2"], deprecated="auto")

    async def hash(self, password: str) -> str:
        return await run_in_threadpool(self._ctx.hash, password)

    async def verify(self, plain: str, hashed: str) -> bool:
        return await run_in_threadpool(self._ctx.verify, plain, hashed)
