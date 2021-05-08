#!/usr/bin/env python3
""" Flask app setup

This module is used to initialize the Flask app with the given
configuration and register handlers.
"""
import os, json
from datetime import date, datetime

from flask import Flask
from flask.json import JSONEncoder
from pandas._libs.tslibs import Timestamp
from plotr_signal.modules.exceptions import AppExceptionHandler

from plotr_signal.routes.root import v1_root
from plotr_signal.routes.equities import v1_equity, v1_equity_price, v1_list_equities, v1_equity_macd, v1_equity_rsi
from plotr_signal.routes.crypto import v1_load_crypto_currencies, v1_load_crypto_products, v1_list_products, v1_get_currency, v1_crypto_load_price_history

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
    app.json_encoder = MinifyJSONEncoder
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

    with app.app_context():
        from plotr_signal.database import db_session, init_db
        init_db()

    # Register api blueprints
    app.register_blueprint(v1_root)
    app.register_blueprint(v1_equity)
    app.register_blueprint(v1_equity_price)
    app.register_blueprint(v1_list_equities)
    app.register_blueprint(v1_equity_macd)
    app.register_blueprint(v1_equity_rsi)
    app.register_blueprint(v1_load_crypto_currencies)
    app.register_blueprint(v1_load_crypto_products)
    app.register_blueprint(v1_list_products)
    app.register_blueprint(v1_get_currency)
    app.register_blueprint(v1_crypto_load_price_history)

    # Register global exception handler
    AppExceptionHandler(app=app)

    @app.route('/health', methods=['GET'])
    def health_check():
        """ Root health check endpoint

        Returns:
            Response: Empty string and status code of 200
        """
        from plotr_signal.modules.influx import Influx
        from plotr_signal.database import db_session

        influxdb_client = Influx()

        return {
            "flask": "online",
            "postgres": db_session.is_active,
            "influxdb": influxdb_client.client.health().status
        }

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app

class MinifyJSONEncoder(JSONEncoder):
    """Used to minify JSON output"""
    item_separator = ','
    key_separator = ':'

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.strftime("%Y-%m-%d %H:%M:%S:%f")
            elif isinstance(obj, date):
                return obj.strftime('%Y-%m-%d')
            elif isinstance(obj, Timestamp):
                return obj.strftime('%Y-%m-%d %H:%M:%S:%f')
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        
        return JSONEncoder.default(self, obj)
