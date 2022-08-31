class NeosException(Exception):
    pass

class NeosAPIException(NeosException):

    def __init__(self, status_code, error_message=""):
        error_message = "[" + str(status_code) + "] API response: " + error_message
        super().__init__(error_message)

class InvalidCredentials(NeosException):
    pass


class NoTokenError(NeosException):
    pass


class FolderNotFound(NeosException):
    pass


class InvalidToken(NeosException):
    pass