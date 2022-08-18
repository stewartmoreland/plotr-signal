#!/usr/bin/env python3

import json

from flask import current_app as app, Blueprint
from flask.globals import request
from markupsafe import escape
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from requests.exceptions import HTTPError


from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)

from plotr_signal.modules.polygon import Polygon

v1_equities = Blueprint('insert-equity', __name__,
                        url_prefix='/api/v1/equities')


@v1_equities.route('/<symbol>', methods=['GET', 'POST', 'DELETE'])
@login_required
def insert_equity(symbol):
    """
    CRUD operations for tracked equities.
    @symbol : str - ticker details to be added for tracking
    """
    from plotr_signal.database import db_session
    from plotr_signal.database.models import Symbols

    if request.method == 'POST':
        try:
            client = Polygon(app.config['POLYGON_API_KEY'])
            resp = client.get_equity_info(symbol)
            equity = Symbols(ticker=resp.symbol,
                             name=resp.name, sector=resp.sector)
        except HTTPError as e:
            raise e

        try:
            db_session.add(equity)
            db_session.commit()
            return {
                "status": "ok",
                "body": f"Successfully entered record for {equity.name}."
            }, 200
        except IntegrityError as e:
            return {
                "status": "DuplicateEntry",
                "body": "Duplicate entry found in table.",
                "message": json.dumps(e.detail)
            }, 400

    elif request.method == 'GET':
        try:
            equity = Symbols.query.filter(Symbols.ticker == symbol).first()
            return {
                "status": "ok",
                "equity": {
                    "ticker": equity.ticker,
                    "name": equity.name,
                    "sector": equity.sector
                }
            }, 200
        except SQLAlchemyError as e:
            return {
                "status": "NoEntryFound",
                "body": f"No entry found for {symbol}",
                "message": json.dumps(e.__dict__)
            }, 400

    elif request.method == 'DELETE':
        try:
            equity = Symbols.query.filter(Symbols.ticker == symbol).first()
            db_session.delete(equity)
            db_session.commit()
            return {
                "status": "ok",
                "body": f"Successfully removed record for {equity.name}"
            }, 200
        except IntegrityError as e:
            return {
                "status": "NoEntryFound",
                "body": f"No entry found for {symbol}",
                "message": json.dumps(e.detail)
            }, 400


@v1_equities.route('/', methods=['GET'])
def get_equities_list():
    """
    Gets list of tracked equities and ticker information.

    No params required as this gets list of all entities in the symbols table.
    """
    from plotr_signal.database.models import Symbols

    response = {"status": "ok", "equities": []}
    response['equities'] = [{"ticker": equity.ticker, "name": equity.name,
                             "sector": equity.sector} for equity in Symbols.query.all()]

    return response, 200


@v1_equities.route('/<symbol>/price', methods=['POST'])
def load_equity_price(symbol):
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

    response = polygon_client.get_historical_data(
        escape(symbol), body['from_'], body['to'])
    results = response.__dict__

    df = DataFrame(data=results['results'])
    df['t'] = to_datetime(df['t'], unit='ms')
    df.rename(columns={'t': 'timestamp'}, inplace=True)
    df.set_index(['timestamp'], inplace=True)
    for column in ['o', 'c', 'h', 'l', 'v', 'vw']:
        df[column] = df[column].astype(float)

    df.rename(columns={
        "o": "open",
        "c": "close",
        "h": "high",
        "l": "low",
        "v": "volume",
        "vw": "weighted_volume"
    }, inplace=True)

    app.logger.info(df.head())

    influx_client.write_dataframe(
        dataframe=df, bucket=symbol, measurement='price')

    return {
        "status": "ok",
        "body": f"Successfully loaded {str(response.resultsCount)} price records for {symbol} from {body['from_']} to {body['to']} into  time series database"
    }, 200


@v1_equities.route('/<symbol>/macd', methods=['POST'])
def load_equity_macd(symbol):
    from plotr_signal.modules.influx import Influx
    from plotr_modules import QuantLib as ql

    body = json.loads(request.get_data())
    influx_client = Influx()
    df = influx_client.get_equity_field_dataframe(
        symbol=symbol, from_=body['from_'], to=body['to'], interval=body['interval'])
    macd = ql.macd(price_data=df)
    influx_client.write_dataframe(
        dataframe=macd, bucket=symbol, measurement='macd')

    return {
        "status": "ok",
        "body": {
            "macd": macd['macd'].to_json(),
            "signal": macd['signal'].to_json()
        }
    }, 200


@v1_equities.route('/<symbol>/rsi', methods=['POST'])
def load_relative_strength_index(symbol):
    from plotr_signal.modules.influx import Influx
    from plotr_modules import QuantLib as ql

    body = json.loads(request.get_data())
    time_period = int

    if 'time_period' in body.keys():
        time_period = body['time_period']
    else:
        time_period = 14

    equity_df = Influx().get_equity_field_dataframe(
        symbol, from_=body['from_'], to=body['to'], interval='15m')
    df = ql.rsi(price_data=equity_df, time_period=time_period)

    Influx().write_dataframe(dataframe=df, bucket=symbol, measurement='rsi')

    return {
        "status": "ok",
        "message": f"Successfully wrote RSI values for {symbol}"
    }, 200
