#!/usr/bin/env python3
""" Route helper methods

This module is used for helping endpoints with the authentication,
authorization, validation, and formatting of requests.
"""
import json
from urllib import request, response, error
from functools import wraps

import hashlib
import hmac
import flask
from flask import current_app as app, request, url_for
from werkzeug.exceptions import Unauthorized, Forbidden, BadRequest

from plotr_signal.exceptions import ValidationAppException


def verify_slack_signature(slack_signature=None, slack_request_timestamp=None):
    """ Verifies the request is from Slack.

    Args:
        slack_signature (str): The signature from the request
        slack_request_timestamp (str): The timestamp from the request
    
    Returns:
        bool: True if the request is from Slack, False otherwise
    """
    req = str.encode('v0:' + str(slack_request_timestamp) + ':') + request.get_data()
    request_hash = 'v0=' + hmac.new(
        str.encode(app.config['SLACK_SIGNING_SECRET']),
        req, hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(request_hash, slack_signature)


def validate_request(schema):
    """ Validates the request against the given schema.

    Args:
        schema (object): The marshmallow schema to validate the request
    
    Returns:
        object: The validated request
    """
    try:
        d = json.loads(flask.request.data)
    except json.JSONDecodeError:
        raise ValidationAppException()
    data, errors = schema().load(d)

    if errors:
        raise ValidationAppException(data=errors)

    return data

