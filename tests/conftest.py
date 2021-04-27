from pytest import fixture
from mock import patch

from plotr_signal.flaskr import create_app
from plotr_signal.conf import Config


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


@fixture(scope='session')
def app(request):
    app = create_app(TestingConfig)
    return app


@fixture(autouse=True)
def app_context(request, app):
    ctx = app.app_context()
    ctx.push()
    yield
    ctx.pop()
