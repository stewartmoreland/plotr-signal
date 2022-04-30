"""
Exception classes for the flask_auth_lib package.

"""

from werkzeug.exceptions import default_exceptions, HTTPException

class AppException(Exception):
    """
    Base class for exceptions in this module.
    """
    description = "An error occurred."

    def __init__(self, data=None, code=400):
        self.data = data
        self.code = code


class ValidationException(AppException):
    description = "The request was invalid."


class InvalidTokenException(AppException):
    description = "The token is invalid, expired, or malformed."
