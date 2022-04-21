"""
Exceptions for the plotr_signal package.
"""

from flask import jsonify
from werkzeug.exceptions import default_exceptions, HTTPException


class AppException(Exception):
    """ 
    Base class for exceptions in this module. 
    """
    description = "An error occurred."

    def __init__(self, data=None, code=400):
        Exception.__init__(self)
        self.data = data
        self.code = code


class ValidationAppException(AppException):
    """
    Exception for validation errors.
    """
    description = "The request was invalid."
