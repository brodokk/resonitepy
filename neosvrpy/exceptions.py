import requests

class NeosException(Exception):
    pass

class NeosAPIException(NeosException):

    def __init__(self, req, message = None):
        if not message:
            message = "[" + str(req.status_code) + "] API response: " + req.text
            message += "\n HEADERS:\n"
            message += str(req.headers)
        super().__init__(message)
        self.status_code = req.status_code
        try:
            self.json = req.json()
        except requests.exceptions.JSONDecodeError:
            print('ee')
            self.json = {}

class InvalidCredentials(NeosException):
    pass


class NoTokenError(NeosException):
    pass


class FolderNotFound(NeosException):
    pass


class InvalidToken(NeosException):
    pass