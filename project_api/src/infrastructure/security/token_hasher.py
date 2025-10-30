import hmac, hashlib

class TokenHasher:
    def __init__(self, pepper: str):
        self.pepper = pepper
    def hash_token(self, token: str) -> str:
        return hmac.new(self.pepper.encode(), token.encode(), hashlib.sha256).hexdigest()