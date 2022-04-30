#!/usr/bin/env python3
""" OAuth endpoints

This module is used for providing endpoints to handle Google OAuth 2.0
authorization with the API.
"""
import os
import json
import requests

from flask import Blueprint, jsonify, redirect, request, url_for
from flask import current_app as app

from sqlalchemy.orm import scoped_session

from oauthlib.oauth2 import WebApplicationClient
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)


v1_oauth = Blueprint('v1_oauth', __name__, url_prefix='/api/auth')


def get_google_provider_cfg():
    return requests.get(os.environ.get("GOOGLE_DISCOVERY_URL")).json()


@v1_oauth.route('/login')
def login():
    """
    Login with Google OAuth 2.0
    """
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    authclient = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = authclient.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@v1_oauth.route("/login/callback")
def callback(db_session:scoped_session=None, user_model=None):
    """
    Handle Google OAuth 2.0 Callback
    """

    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()

    authclient = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])

    token_url, headers, body = authclient.prepare_token_request(
        google_provider_cfg["token_endpoint"],
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_CLIENT_ID'],
              app.config['GOOGLE_CLIENT_SECRET']),
    )

    authclient.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = authclient.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        given_name = userinfo_response.json()["given_name"]
        family_name = userinfo_response.json()["family_name"]
    else:
        return "User email not available or not verified by Google.", 400

    user = user_model.query.filter_by(email=email).first()

    if user:
        login_user(user)
        return redirect(url_for("v1_oauth.login_success"))
    else:
        user = user_model(
            email=email,
            user_name=email,
            given_name=given_name,
            family_name=family_name,
            picture=picture,
            roles=["user"],
            google_id=unique_id
        )
        db_session.add(user)
        db_session.commit()
        login_user(user)
        return redirect(url_for("v1_oauth.login_success"))


@login_required
@v1_oauth.route("/login/success")
def login_success():
    """
    Handle successful login"""
    if current_user.is_authenticated:
        return jsonify(
            user=current_user.to_dict(),
            message="Login successful"
        ), 200
    else:
        return "User is not logged in", 401


@login_required
@v1_oauth.route("/logout")
def logout():
    """
    Handle logout
    """
    logout_user()
    return "User logged out", 200
