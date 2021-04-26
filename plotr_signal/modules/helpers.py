#!/usr/bin/env python3
""" Route helper methods

This module is used for helping endpoints with the authentication,
authorization, validation, and formatting of requests.
"""
import json
from urllib import request, response, error
from functools import wraps
import logging

import hashlib
import hmac
import flask
from flask import current_app as app, request, url_for
from werkzeug.exceptions import Unauthorized, Forbidden, BadRequest

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def verify_slack_signature(slack_signature=None, slack_request_timestamp=None):
    req = str.encode('v0:' + str(slack_request_timestamp) + ':') + request.get_data()
    request_hash = 'v0=' + hmac.new(
        str.encode(app.config['SLACK_SIGNING_SECRET']),
        req, hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(request_hash, slack_signature)
