#!/usr/bin/env python3

import json

from flask import current_app as app, Blueprint, render_template

v1_root = Blueprint('home', __name__)
test_dev_kafka_create_topic = Blueprint('dev-kafka-create-topic', __name__, url_prefix='/test')

@v1_root.route('/', methods=['GET'])
def landing_page():
    return render_template('home.html')

@test_dev_kafka_create_topic.route('/kafka/<topic>', methods=['POST'])
def dev_kafka_create_topic(topic):
    from plotr_signal.modules.kafka import create_topic

    create_topic(app.config['KAFKA_CONF'])
