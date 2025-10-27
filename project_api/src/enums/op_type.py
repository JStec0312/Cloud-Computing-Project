import enum

class OpType(enum.Enum):
    login = "login"
    logout = "logout"
    upload = "upload"
    download = "download"
    list_files = "list_files"
    package_create = "package_create"
    package_download = "package_download"
