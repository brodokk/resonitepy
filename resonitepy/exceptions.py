"""
This module define the Exceptions classes use by this package.
"""

import requests
import json

class ResoniteException(Exception):
    pass

class ResoniteAPIException(ResoniteException):

    def __init__(self, req, message = None):
        if not message:
            message = "[" + str(req.status_code) + "] API response: " + req.text
            message += "\n HEADERS:\n"
            message += str(req.headers)
        super().__init__(message)
        self.status_code = req.status_code
        try:
            self.json = req.json()
        except json.decoder.JSONDecodeError:
            self.json = {}

class InvalidCredentials(ResoniteException):
    pass


class NoTokenError(ResoniteException):
    pass


class FolderNotFound(ResoniteException):
    pass


class InvalidToken(ResoniteException):
    pass

class ResoniteParseError(ResoniteException):
    """ Raised when an API response doesn't match the expected class. """

    def __init__(self, data_class: type, data, error):
        self.data_class = data_class
        self.data = data
        self.error = error
        super().__init__(f"Failed to parse {data_class.__name__}: {error}")

class ResoniteHubException(ResoniteException):
    """ Raised when a hub invocation fails, times out, or the hub is not connected.
    """
    pass