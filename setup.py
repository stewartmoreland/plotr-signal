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
        'flask>=2.1.1',
        'marshmallow==3.15.0',
        'gunicorn~=20.1.0',
        'sqlalchemy~=1.4.35',
        'psycopg2-binary==2.9.3',
        'Werkzeug==2.1.1',
        'apispec==5.1.1',
        'apispec-webframeworks==0.5.2',
        'polygon-api-client==0.2.11',
        'numpy==1.22.3',
        'pandas==1.4.2',
        'sortedcontainers==2.4.0'
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
