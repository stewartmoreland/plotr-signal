#!/usr/bin/env python3
from setuptools import find_packages, setup

test_dependencies = [
        'pytest==6.2.3',
        'pylint==2.9.3',
        'mock==4.0.3',
        'tox==3.24.3'
    ]

extras = {
        'debug': ['ptvsd==4.2.3'],
        'test': test_dependencies,
    }

setup(
    name='plotr-signal-api',
    version='0.0.1',
    description="Plotr Signal API",
    url='https://github.com/stewartmoreland/plotr-signal',
    include_package_data=True,
    install_requires=[
        'flask==1.1.2',
        'sqlalchemy==1.4.11',
        'confluent-kafka==1.7.0',
        'psycopg2-binary==2.8.6',
        'Werkzeug==1.0.1',
        'polygon-api-client==0.1.9',
        'numpy==1.20.2',
        'pandas==1.2.4',
        'sortedcontainers==2.3.0',
        'pydruid[pandas]==0.6.2',
        'celery==5.1.2'
    ],
    setup_requires=[
        'pytest-runner'
    ],
    extras_require=extras,
    tests_require=test_dependencies,
    entry_points={
        'console_scripts': [
            'plotr-signal-api = plotr_signal.main:main',
        ]
    }
)
