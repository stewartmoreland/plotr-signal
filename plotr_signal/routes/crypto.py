#!/usr/bin/env python3

import json
from urllib.parse import quote

from flask import current_app as app, Blueprint
from flask.globals import request
from markupsafe import escape
from datetime import datetime
from numpy.core.fromnumeric import prod

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from requests.exceptions import HTTPError

from plotr_signal.modules import cbpro

v1_load_crypto_currencies = Blueprint('crypto-insert-currencies', __name__, url_prefix='/v1')
v1_load_crypto_products = Blueprint('crypto-insert-products', __name__, url_prefix='/v1')
v1_get_currency = Blueprint('crypto-get-currency', __name__, url_prefix='/v1')
v1_crypto_load_price_history = Blueprint('crypto-load-price-history', __name__, url_prefix='/v1')
v1_list_crypto = Blueprint('crypto-list-currencies', __name__, url_prefix='/v1')
v1_list_products = Blueprint('crypto-list-products', __name__, url_prefix='/v1')

@v1_load_crypto_currencies.route('/crypto/import/currencies', methods=['POST'])
def load_crypto_currencies():
    """
    Adds currencies supported by Coinbase Pro.
    """
    from plotr_signal.database import db_session
    from plotr_signal.database.models import CryptoCurrencies

    try:
        client = cbpro.PublicClient()
        response = client.get_currencies()
    except HTTPError as e:
        raise e
    
    try:
        for resp in response:
            equity = CryptoCurrencies(currency=resp['id'],
                                    name=resp['name'],
                                    min_size=resp['min_size'])
            db_session.merge(equity)
            db_session.commit()
        return {
            "status": 200,
            "body": json.dumps(response)
        }
    except IntegrityError as e:
        raise e

@v1_load_crypto_products.route('/crypto/import/products', methods=['POST'])
def load_crypto_products():
    from plotr_signal.database import db_session
    from plotr_signal.database.models import CryptoProducts

    try:
        client = cbpro.PublicClient()
        response = client. get_products()
    except HTTPError as e:
        raise e

    try:
        for resp in response:
            product = CryptoProducts(product=resp['id'],
                                    name=resp['display_name'],
                                    base_currency=resp['base_currency'],
                                    quote_currency=resp['quote_currency'],
                                    base_min_size=resp['base_min_size'],
                                    base_max_size=resp['base_max_size'])
            db_session.merge(product)
            db_session.commit()
        return {
            "status": 200,
            "message": f"Successfully loaded crypto products from Coinbase Pro",
            "products": json.dumps(response)
        }
    except IntegrityError as e:
        raise e

@v1_get_currency.route('/crypto/<currency>', methods=['GET'])
def get_currency_details(currency:str):
    from plotr_signal.database.models import CryptoCurrencies

@v1_list_products.route('/crypto/products/<quote_currency>', methods=['GET'])
def get_equities_list(quote_currency):
    """
    Gets list of tracked crypto currencies and ticker information.

    No params required as this gets list of all entities in the symbols table.
    """
    from plotr_signal.database.models import CryptoProducts

    equities = CryptoProducts.query.filter(CryptoProducts.quote_currency == quote_currency).all()

    response = { "status": 200, "equities": [] }
    for equity in equities:
        response['equities'].append({ "product": equity.product, "name": equity.name, "base_currency": equity.base_currency, "quote_currency": equity.quote_currency })
    
    return response

@v1_crypto_load_price_history.route('/crypto/<product>/price/history', methods=['POST'])
def equity_price(product):
    """
    Posts price details to time series database as a Pandas DataFrame for the requested ticker symbol.
    @symbol : str - path parameter for the desired ticker symbol to be imported
    @method : POST
    @body : { "from_": "yyyy-mm-dd", "to": "yyyy-mm-dd" }
    """
    from plotr_signal.modules.influx import Influx
    from pandas import DataFrame

    public_client = cbpro.PublicClient()
    influx_client = Influx()
    body = json.loads(request.get_data())

    response = public_client.get_product_historic_rates(product_id=product, start=body['from_'], end=body['to'])
    app.logger.info(response)

    # influx_client.write_dataframe(dataframe=df, bucket=symbol)

    return {
        "status": 200,
        # "body": f"Successfully loaded time series pricing data for {symbol} from {body['from_']} to {body['to']}"
    }
