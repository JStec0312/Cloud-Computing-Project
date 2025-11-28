
from src.config.app_config import settings
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

class RefreshTokenError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        
class RefreshTokenMissingError(RefreshTokenError):
    def __init__(self, detail: str = "Refresh token is missing"):
        super().__init__(status_code=401, detail=detail)
        
class MissingAccessTokenError(Exception):
    def __init__(self, detail: str = "Access token is missing"):
        self.status_code = 401
        self.detail = detail
        
class TokenExpiredError(Exception):
    def __init__(self, detail: str = "Token has expired"):
        self.status_code = 401
        self.detail = detail
        
class InvalidTokenError(Exception):
    def __init__(self, detail: str = "Invalid token"):
        self.status_code = 401
        self.detail = detail

class InvalidParentFolder(Exception):
    def __init__(self, folder_id: str, detail: str = "Invalid parent folder"):
        self.status_code = 404
        self.detail = f"Parent folder with id {folder_id} not found."

class FileTooLargeError(Exception):
    def __init__(self, max_size_mb: int = settings.max_file_upload_size_mb):
        self.status_code = 413
        self.detail = f"File size exceeds the maximum allowed size of {max_size_mb} MB."

class FolderNotFoundError(Exception):
    def __init__(self, folder_id: str):
        self.status_code = 404
        self.detail = f"Folder with id {folder_id} not found."

class FileNameExistsError(Exception):
    def __init__(self,  detail: str = "File name already exists in the target folder"):
        self.status_code = 409
        self.detail = detail 
        
class FileNotFoundError(Exception):
    def __init__(self, detail: str = "File not found"):
        self.status_code = 404
        self.detail = detail

class AccessDeniedError(Exception):
    def __init__(self, detail: str = "Access denied"):
        self.status_code = 403
        self.detail = detail