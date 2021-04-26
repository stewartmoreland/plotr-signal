#!/usr/bin/env python3
import os

from plotr_signal.flaskr import create_app
from plotr_signal.conf import config

def main():
    environment_name = os.environ.get('ENVIRONMENT', 'default')
    config_object = config[environment_name]
    app = create_app(config_object)

    app.run(host='0.0.0.0', port=app.config['PORT'])

if __name__ == '__main__':
    main()
