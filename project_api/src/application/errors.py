
class UserError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

class UserAlreadyExistsError(UserError):
    def __init__(self, email: str):
        super().__init__(status_code=409, detail=f"User with email {email} already exists.")

class UserNotFoundError(UserError):
    def __init__(self, email: str):
        super().__init__(status_code=404, detail=f"User with email {email} not found.")

class InvalidCredentialsError(UserError):
    def __init__(self):
        super().__init__(status_code=401, detail="Invalid email or password.")