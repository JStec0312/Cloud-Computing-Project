import hashlib
class TokenHasher:
    def __init__(self, pepper: str):
        self.pepper = pepper
    def hash_token(self, token: str) -> str:
        return hashlib.sha256((token + self.pepper).encode()).hexdigest()