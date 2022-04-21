#!/usr/bin/env python3
""" Flask app setup

This module is used to initialize the Flask app with the given
configuration and register handlers.
"""
import os, json
from datetime import date, datetime

from flask import Flask, jsonify, render_template
from flask.json import JSONEncoder

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from pandas._libs.tslibs.timestamps import Timestamp
from plotr_signal.modules.exceptions import AppExceptionHandler

from plotr_signal.routes import *


def create_app(config_object):
    """ Basic application factory for setting up the Flask app

    Args:
        config_object (object): The config object to load into the
            Flask app
        config_object (string): The string path to the config object
            to load into the flask app
    
    Returns:
        app (object): The Flask app post-setup
    """
    app = Flask(__name__)

    app.config.from_object(config_object)

    # Configuration to minify JSON output
    app.json_encoder = CustomJSONEncoder
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

    with app.app_context():
        from plotr_signal.database import db_session, init_db
        init_db()

    # Register api blueprints
    app.register_blueprint(v1_root)
    app.register_blueprint(v1_equities)
    app.register_blueprint(v1_crypto)

    # Register global exception handler
    AppExceptionHandler(app=app)

    def add_paths_for_blueprint(spec, blueprint, exclude=()):
        bp_name = blueprint.name
        for r in app.url_map.iter_rules():
            ep = r.endpoint.split('.')
            if len(ep) == 1:  # App endpoint, not processed here
                break
            elif len(ep) == 2:  # Blueprint endpoint
                prefix, endpoint = ep[0], ep[1]
                if prefix == bp_name and endpoint not in exclude:
                    spec.path(view=app.view_functions[r.endpoint])
            else:
                raise ValueError("Not valid endpoint?", r.endpoint)

    @app.route('/health', methods=['GET'])
    def health_check():
        """ Root health check endpoint
        
        Returns:
            json (dict): A dictionary containing the health of the
                application
        """
        from plotr_signal.database import db_session

        return jsonify({
            "flask": "OK",
            "postgres": db_session.is_active
        }), 200

    @app.route('/apispec.json', methods=['GET'])
    def get_swagger_json():
        """ Get swagger json for the API
        """
        spec = APISpec(
            title="plotr: Signal Analysis API",
            version="1.0.0",
            openapi_version="3.0.2",
            plugins=[FlaskPlugin(), MarshmallowPlugin()],
        )
        add_paths_for_blueprint(spec, v1_root, exclude=['get_swagger_json'])
        add_paths_for_blueprint(spec, v1_equities, exclude=['get_swagger_json'])
        add_paths_for_blueprint(spec, v1_crypto, exclude=['get_swagger_json'])
        return jsonify(spec.to_dict()), 200
    
    @app.route('/apispec', methods=['GET'])
    def get_swagger_ui():
        """ Serve the swagger docs from the /apispec directory

        Args:
            path (string): The path to the swagger docs

        Returns:
            Response: The swagger docs
        """
        app.logger.info('Serving docs')
        return render_template('swaggerui.html')

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app

class MinifyJSONEncoder(JSONEncoder):
    """Used to minify JSON output"""
    item_separator = ','
    key_separator = ':'

class CustomJSONEncoder(JSONEncoder):
    def _encode(self, obj):
        if isinstance(obj, dict):
            def transform_date(o):
                return self._encode(o.isoformat() if isinstance(o, datetime) else o)
            return {transform_date(k): transform_date(v) for k, v in obj.items()}
        else:
            return obj

    def encode(self, obj):
        return super(CustomJSONEncoder, self).encode(self._encode(obj))

    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.strftime("%Y-%m-%dT%H:%M:%S.%f")
            elif isinstance(obj, date):
                return obj.strftime("%Y-%m-%d")
            elif isinstance(obj, Timestamp):
                return obj.strftime("%Y-%m-%dT%H:%M:%S.%f")
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
