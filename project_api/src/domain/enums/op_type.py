import enum

class OpType(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    AUTO_AUTH = "auto_auth"  # <--- ADD THIS LINE
    UPLOAD = "upload"
    DOWNLOAD = "download"
    LIST_FILES = "list_files"
    PACKAGE_CREATE = "package_create"
    PACKAGE_DOWNLOAD = "package_download"
    USER_REGISTER = "user_register"
    REFRESH_TOKEN="refresh_token"
    FILE_UPLOAD_ATTEMPT="file_upload_attempt"
    RENAME="rename"
    FILE_DELETE="file_delete"
    VIEW_FILE_VERSIONS="view_file_versions"
    FOLDER_CREATE="folder_create"