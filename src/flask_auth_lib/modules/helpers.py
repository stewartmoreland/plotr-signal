#!/usr/bin/env python3
""" Route helper methods

This module is used for helping endpoints with the authentication,
authorization, validation, and formatting of requests.
"""
import json
import requests
from functools import wraps

from flask import (
    current_app as app,
    request, 
    session, 
    abort, 
    make_response, 
    jsonify,
    url_for
)

from flask_login import login_required

from oauthlib.oauth2 import WebApplicationClient
from oauthlib.oauth2 import BearerToken

from werkzeug.exceptions import Unauthorized, Forbidden, BadRequest


# def require_auth():
#     """ Require a valid bearer token to be present in the request header.

#     Raises:
#         Unauthorized: If no token is present in the request header

#     Returns:
#         Response: Serialized JSON with status code and json
#     """
#     auth_header = request.headers.get('Authorization')
#     if not auth_header:
#         abort(401)
#         return None
    
#     token = get_bearer_token_from_header(auth_header)

#     email = None
#     if is_jwt_token(token):
#         id_info = validate_id_token(token)  
#         email = id_info['email'] 
#     else:
#         validate_access_token(token)
#         userinfo = get_userinfo(token)
#         email = userinfo.email
    
#     user = get_user_by_email(email)
#     if user is None:
#         raise Unauthorized("User '%s' is not a registered user." % email)

#     session['user'] = user_session_mapper(user)
#     session['token'] = token


def require_role(roles:list=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            """ Decorator function used at the endpoint method to require role 
            authorization before the endpoint is hit.

            Args:
                roles (list): list of roles that are allowed to access the
                endpoint
            
            Raises:
                Unauthorized: If user does not have the required role
            
            Session:
                user (dict): User session data
            """
            ALLOW_ALL_ROLES = ['*']
            endpoint = url_for(request.endpoint)
            user = session['user']

            if not user:
                raise Unauthorized(
                    'User is not logged in. Please login to access endpoint: %s'
                    % endpoint)
            if not user['is_enabled']:
                raise Unauthorized(
                    "User '%s' is disabled" % user['email'])
            if user['role'] not in roles and ALLOW_ALL_ROLES != roles:
                raise Forbidden(
                    "User '%s' is unauthorized to access API endpoint '%s'" % (user['email'], endpoint))
            
            app.logger.info(
                f"User {user['email']} authorized on endpoint {endpoint} with role {user['role']}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_bearer_token_from_header(auth_header):
    """ Checks if the authorization header is a valid Bearer token.

    Args:
        auth_header (str): Authorization header from request
    
    Returns:
        token (str): Parsed token from header

    Raises:
        InvalidTokenException: If 'token' is not a Bearer token or is
        None
    """
    if auth_header is None:
        raise InvalidTokenException()

    BEARER_PREFIX = 'Bearer'

    prefix, _, token = auth_header.partition(' ')

    if BEARER_PREFIX != prefix:
        raise InvalidTokenException()
    return token


def validate_access_token(token):
    """ Validates if the token against Google API's token info and the
    application's Google API Client Config for OAuth.

    Raises:
        Unauthorized: If 'token' is invalid/expired or if 'token' was
        not issued by the application
    """
    r = requests.post('https://www.googleapis.com/oauth2/v1/tokeninfo',
        params = {'access_token': token},
        headers = {'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(r, 'status_code')
    data = json.loads(r.content)

    if status_code == 200:
        if data['issued_to'] != app.config['GOOGLE_API_CLIENT_ID'] or \
            data['audience'] != app.config['GOOGLE_API_CLIENT_ID'] or \
            data['scope'] != app.config['GOOGLE_API_OAUTH_SCOPES']:
            raise Unauthorized('Unauthorized bearer token')
    else:
        error_description = data['error_description']
        raise Unauthorized(error_description)


def get_userinfo(token):
    """ Retrieves user info from Google API. Relies on scopes userinfo
    email and profile to have been authorized for the given token.

    Args:
        token (string): User bearer token
    
    Returns:
        GoogleApiUserInfo: Google API response for the /userinfo endpoint
    """
    r = requests.get('https://www.googleapis.com/oauth2/v1/userinfo',
        params = {'access_token': token},
        headers = {'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(r, 'status_code')
    data = json.loads(r.content)

    if status_code == 200:
        return GoogleApiUserInfo(data)
    else:
        error_description = data.get('error_description')
        raise InvalidTokenException(error_description)


def validate_id_token(token):
    """ Validates if the token is a valid ID token issued by the application.

    Args:
        token (string): User bearer token

    Returns:
        GoogleApiUserInfo: Google API response for the /userinfo endpoint
    """
    try:
        # id_info = id_token.verify_oauth2_token(
        #     token, google.auth.transport.requests.Request(), app.config['GOOGLE_API_CLIENT_ID'])
        id_info = 
    except:
        raise InvalidTokenException('Invalid id_token')
    
    if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        raise InvalidTokenException('Wrong issuer for id_token')

    if id_info['hd'] != app.config['HOSTED_DOMAIN']:
        raise InvalidTokenException('Wrong hosted domain for id_token')
    
    if not id_info['email_verified']:
        raise InvalidTokenException('Unverified email for id_token')
        
    return id_info


def handle_response(data, message=None, code=200):
    """ Jsonifies a successful response with the same json
    payload structure.

    Args:
        data (dict/int/string): data to pass back as json
        message (string): optional message to send back as response
        code (int): successful http status code

    Returns:
        Response: Serialized JSON with status code and json
        header set
    """
    response = {}
    if data:
        response['data'] = data
    if message:
        response['message'] = message

    return jsonify(response), code

def respond(data, code=200):
    """ Tells Flask to return a response to the calling user.

    Args:
        data (dict/int/string): The object to return (will be converted to JSON)
        code (int): The HTTP status code of the response
    
    Returns:
        response: The built response object
    """
    return make_response(jsonify(data), code)

def is_jwt_token(token):
    """ Checks if token string is formatted as a jwt. This
    does NOT validate the jwt

    Args:
        token (string): any bearer token

    Returns:
        Response: Serialized JSON with status code and json
        header set
    """
    arr = token.split('.')
    return len(arr) == 3
