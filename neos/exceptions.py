class NeosException(Exception):
    pass


class NoTokenError(NeosException):
    pass


class FolderNotFound(NeosException):
    pass