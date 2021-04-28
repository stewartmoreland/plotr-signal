#!/usr/bin/env python3

import json

from flask import current_app as app, Blueprint
from flask.globals import request
from markupsafe import escape
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from requests.exceptions import HTTPError

from plotr_signal.modules.polygon import Polygon

v1_equity = Blueprint('insert-equity', __name__, url_prefix='/v1')
v1_equity_price = Blueprint('insert-equity-price-data', __name__, url_prefix='/v1')
v1_list_equities = Blueprint('list-equities', __name__, url_prefix='/v1')

@v1_equity.route('/equities/<symbol>', methods=['GET','POST'])
def insert_equity(symbol):
    """
    Adds ticker symbol to be tracked.
    @symbol : str - ticker details to be added for tracking
    """
    from plotr_signal.database import db_session
    from plotr_signal.database.models import Symbols

    if request.method == 'POST':
        try:
            client = Polygon(app.config['POLYGON_API_KEY'])
            resp = client.get_equity_info(symbol)
            equity = Symbols(ticker=resp.symbol, name=resp.name, sector=resp.sector)
        except HTTPError as e:
            raise e

        try:
            db_session.add(equity)
            db_session.commit()
            return {
                "status": 200,
                "body": f"Successfully entered record for {symbol}."
            }
        except IntegrityError as e:
            return {
                "status": 400,
                "body": "Duplicate entry found in table."
            }

    elif request.method == 'GET':
        try:
            equity = Symbols.query.filter(Symbols.ticker == symbol).first()
            return {
                "status": 200,
                "equity": {
                    "ticker": equity.ticker,
                    "name": equity.name,
                    "sector": equity.sector
                }
            }
        except SQLAlchemyError as e:
            return {
                "status": 400,
                "body": "No equity found from ticker value"
            }

@v1_list_equities.route('/equities', methods=['GET'])
def get_equities_list():
    """
    Gets list of tracked equities and ticker information.

    No params required as this gets list of all entities in the symbols table.
    """
    from plotr_signal.database.models import Symbols

    response = { "status": 200, "equities": [] }
    equities = Symbols.query.all()

    for equity in equities:
        response['equities'].append({ "ticker": equity.ticker, "name": equity.name, "sector": equity.sector })
    
    return response

@v1_equity_price.route('/equities/<symbol>/price', methods=['POST'])
def equity_price(symbol):
    """
    Posts price details to time series database as a Pandas DataFrame for the requested ticker symbol.
    @symbol : str - path parameter for the desired ticker symbol to be imported
    @method : POST
    @body : { "from_": "yyyy-mm-dd", "to": "yyyy-mm-dd" }
    """
    from plotr_signal.modules.influx import Influx
    from pandas import DataFrame, to_datetime

    polygon_client = Polygon(app.config['POLYGON_API_KEY'])
    influx_client = Influx()
    body = json.loads(request.get_data())

    response = polygon_client.get_historical_data(escape(symbol), body['from_'], body['to'])
    app.logger.info(response)

    for result in response.results:
        result['t'] = datetime.fromtimestamp(result['t']/1000.0)
        df = DataFrame(data=result, index=[result['t']])
        df['o'] = df['o'].astype(float)
        df['c'] = df['c'].astype(float)
        df['h'] = df['h'].astype(float)
        df['l'] = df['l'].astype(float)
        df['v'] = df['v'].astype(float)
        df['vw'] = df['vw'].astype(float)
        
        influx_client.write_dataframe(dataframe=df, bucket=symbol)

    return {
        "status": 200,
        "body": f"Successfully loaded time series pricing data for {symbol} from {body['from_']} to {body['to']}"
    }
