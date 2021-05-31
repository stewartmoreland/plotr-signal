#!/usr/bin/env python3
""" Application configuration

This module is used to provide environment-based configuration objects
for the flask application context on start up.
"""
import os
import json
import socket

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    """ Base Flask configuration object. Base should always
    assume to be Production.
    """
    SESSION_COOKIE_SECURE = True
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'tmp/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')
    INFLUXDB_V2_URL = os.environ.get('INFLUXDB_V2_URL')
    INFLUXDB_V2_ORG = os.environ.get('INFLUXDB_V2_ORG')
    INFLUXDB_V2_ORG_ID = os.environ.get('INFLUXDB_V2_ORG_ID')
    INFLUXDB_V2_TOKEN = os.environ.get('INFLUXDB_V2_TOKEN')
    DRUID_HOST = os.environ.get('DRUID_HOST')

    KAFKA_CONF = { 'bootstrap.servers': os.environ.get('KAFKA_SERVERS'),
                   'client.id': socket.gethostname() }


class ProductionConfig(Config):
    """ Producation configuration object. Similar to base config, used for
    readability. 
    """
    PORT = os.environ.get('PORT')


class LocalConfig(Config):
    """ Local configuration object for local development.
    """
    DEBUG = True
    PORT = 5000
    URL_SCHEME = 'http'
    SESSION_COOKIE_SECURE = False
    INFLUXDB_V2_VERIFY_SSL = False


config = {
    'LOCAL': LocalConfig,
    'PRODUCTION': ProductionConfig,
    'default': LocalConfig
}
""" dict: For string key to object config mapping
"""
