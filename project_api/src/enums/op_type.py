import enum

class OpType(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    LIST_FILES = "list_files"
    PACKAGE_CREATE = "package_create"
    PACKAGE_DOWNLOAD = "package_download"
    USER_REGISTER = "user_register"
