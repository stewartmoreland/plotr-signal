#!/usr/bin/env python3
from setuptools import find_packages, setup

setup(
    name='plotr-signal-api',
    version='0.0.1',
    description="Plotr Signal API",
    url='https://github.com/stewartmoreland/plotr-signal',
    include_package_data=True,
    install_requires=[
        'flask==1.1.2',
        'sqlalchemy==1.4.11',
        'psycopg2-binary==2.8.6',
        'Werkzeug==1.0.1',
        'influxdb-client[ciso]==1.16.0',
        'polygon-api-client==0.1.9',
        'numpy==1.20.2',
        'pandas==1.2.4',
        'sortedcontainers==2.3.0'
    ],
    setup_requires=[
        'pytest-runner'
    ],
    extras_require={
        'debug': ['ptvsd==4.2.3']
    },
    tests_require=[
        'pytest==6.2.3',
        'mock==4.0.3'
    ],
    entry_points={
        'console_scripts': [
            'plotr-signal-api = plotr_signal.main:main',
        ]
    }
)
