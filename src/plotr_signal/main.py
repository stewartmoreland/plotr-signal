#!/usr/bin/env python3

import os

from logging.config import dictConfig

from plotr_signal.flaskr import create_app
from plotr_signal.conf import config


def main():
    environment_name = os.environ.get('ENVIRONMENT', 'default')
    config_object = config[environment_name]

    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })

    app = create_app(config_object)

    app.run(host='0.0.0.0', port=app.config['PORT'])


if __name__ == '__main__':
    main()
