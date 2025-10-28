from fastapi import HTTPException
class UserError(HTTPException):
    # Base class for user-related exceptions
    pass

class UserAlreadyExistsError(UserError):
    def __init__(self, email: str):
        super().__init__(status_code=400, detail=f"User with email {email} already exists.")