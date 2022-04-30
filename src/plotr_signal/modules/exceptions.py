#!/usr/bin/env python3
""" Application level exception handling

This module is used to provide a global exception handler for all
exceptions, as well as provide additional exceptions for application-
specific scenarios.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException


DEFAULT_ERROR_CODE = 500
DEFAULT_ERROR_MESSAGE = "An unexpected error has occurred."


class AppExceptionHandler():
    """ Global exception handler that will be registered with the Flask
    application context

    Attributes:
        app (object): Current Flask application
    """
    def __init__(self, app=None):
        self.app = app
        self.register(HTTPException)
        for _, obj in default_exceptions.items():
            self.register(obj)
        self.register(Exception)


    def register(self, exception):
        """ Register the handler with Flask for the exception that should be
        handled

        Args:
            exception (object): The exception that will be raised
        """
        self.app.register_error_handler(exception, self.handler)


    def handler(self, e):
        """ Default handler for when a registered exception is raised

        Args:
            e (object): Exception that was raised

        Returns:
            Response: Jsonifies an unsuccessful response with the same
            JSON payload structure
        """
        status_code = e.code if hasattr(e, 'code') else DEFAULT_ERROR_CODE
        error = e.description if hasattr(e, 'description') else DEFAULT_ERROR_MESSAGE

        response = {}
        response['error'] = error
        if hasattr(e, 'data'):
            response['data'] = e.data

        if self.app.debug:
            response['debug'] = str(e)

        logging.fatal(e, exc_info=True)

        return jsonify(response), status_code


class AppException(Exception):
    """ Base exception class for application-specific exceptions

    Attributes:
        data (object): Error-related data to pass back to the user
    """
    description = "An application-level exception has occurred."

    def __init__(self, data=None, code=400):
        self.data = data
        self.code = code

