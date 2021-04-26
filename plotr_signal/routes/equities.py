#!/usr/bin/env python3

import json

from flask import current_app as app, Blueprint
from flask.globals import request
from markupsafe import escape

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from requests.exceptions import HTTPError

from plotr_signal.modules.polygon import Polygon

v1_insert_equity = Blueprint('insert-equity', __name__)
v1_insert_equity_price = Blueprint('insert-equity-price-data', __name__)

@v1_insert_equity.route('/insert/<symbol>', methods=['POST'])
def insert_equity(symbol):
    from plotr_signal.database import db_session
    from plotr_signal.database.models import Symbols
    client = Polygon(app.config['POLYGON_API_KEY'])
    resp = client.get_equity_info(symbol)

    try:
        equity = Symbols(ticker=resp.symbol, name=resp.name, sector=resp.sector)
    except HTTPError as e:
        raise e

    try:
        db_session.add(equity)
        db_session.commit()
        response = { "status": 200, "body": f"Successfully entered record for {symbol}." }
    except IntegrityError as e:
        response = { "status": 400, "body": "Duplicate entry found in table." }
        raise e

    return json.dumps(response, indent=4)

@v1_insert_equity_price.route('/insert/<symbol>/price', methods=['POST'])
def insert_equity_price(symbol):
    client = Polygon(app.config['POLYGON_API_KEY'])
    body = json.loads(request.get_data())

    response = client.get_historical_data(escape(symbol), body['from_'], body['to'])
    app.logger.info(response)

    return {
        "status": 200,
        "body": json.dumps("Successfully loaded data for " + symbol)
    }
