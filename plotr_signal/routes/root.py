#!/usr/bin/env python3

import json

from flask import current_app as app, Blueprint, render_template

v1_root = Blueprint('home', __name__)

@v1_root.route('/', methods=['GET'])
def landing_page():
    return render_template('home.html')

