#!/usr/bin/env python3
"""
Crypto routes for the Plotr Signal API
"""

from asyncio.log import logger
from flask import current_app as app, Blueprint
from flask import jsonify, json
from flask.globals import request
from pandas.core.tools.datetimes import to_datetime

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from requests.exceptions import HTTPError

from plotr_signal.modules import cbpro


v1_crypto = Blueprint('crypto-insert-currencies', __name__, url_prefix='/api/v1/crypto')


@v1_crypto.route('/import/currencies', methods=['POST'])
def load_crypto_currencies():
    """
    Adds currencies supported by Coinbase Exchange/Pro.

    @symbol : str - ticker details to be added for tracking

    Returns:
        dict: JSON response
    """
    from plotr_signal.database import db_session
    from plotr_signal.database.models import CryptoCurrencies

    try:
        client = cbpro.PublicClient()
        response = client.get_currencies()
    except HTTPError as e:
        raise e

    try:
        equities = [
            CryptoCurrencies(currency=resp['id'],
                             name=resp['name'],
                             min_size=resp['min_size'])
            for resp in response]
        db_session.bulk_save_objects(equities)
        db_session.commit()
        return jsonify(response), 200
    except IntegrityError as e:
        raise e


@v1_crypto.route('/import/products', methods=['POST'])
def load_crypto_products():
    """
    Adds products supported by Coinbase Exchange/Pro.
    
    @symbol : str - ticker details to be added for tracking

    Returns:
        dict: JSON response
    """
    from plotr_signal.database import db_session
    from plotr_signal.database.models import CryptoProducts

    try:
        client = cbpro.PublicClient()
        response = client.get_products()
    except HTTPError as e:
        raise e

    try:
        products = [
            CryptoProducts(product=resp['id'],
                           name=resp['display_name'],
                           base_currency=resp['base_currency'],
                           quote_currency=resp['quote_currency'],
                           base_min_size=resp['base_min_size'],
                           base_max_size=resp['base_max_size'])
            for resp in response]
        db_session.bulk_save_objects(products)
        db_session.commit()
        return jsonify({"message": f"Successfully loaded crypto products from Coinbase Pro",
            "products": response}), 200
    except IntegrityError as e:
        raise e


@v1_crypto.route('/import/history', methods=['POST'])
def crypto_import_price_history():
    '''
    Imports historical price data for a given product.

    @symbol : str - ticker details to be added for tracking

    Returns:
        dict: JSON response
    '''
    from plotr_signal.modules.crypto import get_crypto_price_history
    from plotr_signal.modules.druid import PlotrDruid, build_task_ingestion_spec
    from pandas import DataFrame
    from datetime import date, datetime

    druid = PlotrDruid(druid_host=app.config['DRUID_HOST'])
    
    data = dict(json.loads(request.get_data()))
    start = datetime.combine(date.fromisoformat(data['from_']), datetime.min.time())
    end = datetime.combine(date.fromisoformat(data['to']), datetime.max.time())

    app.logger.info(f"Fetching price history for {request.args['product']}")
    results = get_crypto_price_history(product=request.args['product'], start=start, end=end)
    results['time'] = results['time'].dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

    app.logger.info(f"Building task ingestion spec for {request.args['product']}")
    spec = build_task_ingestion_spec(product=request.args['product'], data=results.to_dict(orient='records'))
    app.logger.info("Submitting task spec to Druid")
    response = druid.submit_ingestion_task(json.dumps(spec))

    return jsonify(response), 200


@v1_crypto.route('/<product>/stablecoin', methods=['POST'])
def set_stablecoin(product: str):
    """
    Sets the stablecoin for a given product.

    @product : str - product to set the stablecoin for

    Returns:
        dict: JSON response
    """
    from plotr_signal.database import db_session
    from plotr_signal.database.models import CryptoProducts

    body = dict(json.loads(request.get_data()))
    equity = CryptoProducts.query.filter(
        CryptoProducts.product == product).first()

    if 'set' in body.keys() and body['set'] is True:
        equity.stablecoin = True
        db_session.commit()

        return {"status": 200, "message": f"Set {product} as stablecoin"}
    elif 'set' in body.keys() and body['set'] is False:
        equity.stablecoin = False
        # db_session.merge(equity)
        db_session.commit()

        return jsonify({"message": f"Unset {product} as stablecoin"}), 200
    else:
        return jsonify({"message": f"set missing from request body"}), 400


@v1_crypto.route('/<currency>', methods=['GET'])
def get_currency_details(currency: str):
    """
    Gets the details for a given currency.

    @currency : str - currency to get details for

    Returns:
        dict: JSON response
    """
    from plotr_signal.database.models import CryptoCurrencies
    equity = CryptoCurrencies.query.filter(
        CryptoCurrencies.currency == currency).first()
    return {"currency": equity.currency, "name": equity.name, "min_size": equity.min_size}


@v1_crypto.route('/products', methods=['GET'])
def get_equities_list():
    """
    Gets list of tracked crypto currencies and ticker information.
    
    Returns:
        dict: JSON response
    """
    from plotr_signal.database.models import CryptoProducts

    stablecoin = bool
    if 'stablecoin' not in request.args.keys() or request.args.get('stablecoin') == "false":
        stablecoin = False
    elif 'stablecoin' in request.args.keys() and request.args.get('stablecoin') == "true":
        stablecoin = True

    if 'quote_currency' in request.args.keys():
        quote_currency = request.args.get('quote_currency')
        equities = CryptoProducts.query.filter(
            CryptoProducts.quote_currency == quote_currency,
            CryptoProducts.stablecoin == stablecoin).all()
    else:
        equities = CryptoProducts.query.filter(
            CryptoProducts.stablecoin == stablecoin).all()

    response = [{"product": equity.product, "name": equity.name,
                             "base_currency": equity.base_currency, "quote_currency": equity.quote_currency,
                             "supervised": equity.supervised} for equity in equities]

    return jsonify(response), 200


@v1_crypto.route('/<product>/price/history', methods=['POST'])
def crypto_load_price_history(product):
    """
    Posts price details to time series database as a Pandas DataFrame for the requested ticker symbol.
    
    @product : str - ticker details to be added for tracking
    @body : { "from_": "yyyy-mm-ddThh:mm:ss.xxx", "to": "yyyy-mm-ddThh:mm:ss.xxx", "interval": "60|300|900|3600|21600|86400" }

    Returns:
        dict: JSON response
    """
    from plotr_signal.modules.influx import Influx
    from pandas import DataFrame
    # from plotr_signal.modules.kafka import KafkaProducer, KafkaError
    from datetime import date, datetime, timedelta

    public_client = cbpro.PublicClient()
    # producer = KafkaProducer(conf=app.config['KAFKA_CONF'])
    ts_db = Influx()
    data = json.loads(request.get_data())

    response = []
    current_dt = datetime.combine(date.fromisoformat(data['from_']), datetime.min.time())
    to_dt = datetime.combine(date.fromisoformat(data['to']), datetime.max.time())
    delta = timedelta(minutes=300)
    
    while current_dt < to_dt:
        app.logger.info("Fetching price history for {}".format(product))
        end_datetime = current_dt + delta
        response.extend(public_client.get_product_historic_rates(
            product_id=product, start=current_dt, end=end_datetime, granularity=data['interval']))
        current_dt = current_dt + delta
    
    app.logger.debug(response)
    app.logger.info("Building task ingestion spec for {}".format(product))

    df = DataFrame(data=response, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
    df['time'] = to_datetime(df['time'], unit='s')
    df.set_index(df['time'], drop=True, inplace=True)
    for column in ['low', 'high', 'open', 'close', 'volume']:
        df[column] = df[column].astype(float)

    df['price'] = df[['low', 'high', 'open', 'close']].mean(axis=1)

    # ts_db.write_dataframe(df, measurement=product)

    # try:
    #     for idx, row in df.iterrows():
    #         app.logger.info(f"{idx}: {row.to_json()}")
    #         producer.write_msg(
    #             topic=product, msg=row.to_json(), timestamp=row['time'])
    # except KafkaError as e:
    #     app.logger.error("Generic error writing to Kafka: {}".format(e))

    return jsonify(df.to_dict(orient='index')), 200


@v1_crypto.route('/<product>/supervise', methods=['POST'])
def supervise_product(product: str):
    """
    Sets the supervised flag for a given product.

    @product : str - product to set the supervised flag for

    Returns:
        dict: JSON response
    """
    from plotr_signal.database import db_session
    from plotr_signal.database.models import CryptoProducts

    # from plotr_signal.modules.kafka import KafkaAdmin
    # from plotr_signal.modules.druid import PlotrDruid, build_kafka_supervisor_spec

    from plotr_signal.database import db_session
    from plotr_signal.database.models import CryptoProducts

    body = dict(json.loads(request.get_data()))
    equity = CryptoProducts.query.filter(
        CryptoProducts.product == product).first()

    if 'supervised' in body.keys() and body['supervised'] is True:
        equity.supervised = True
        db_session.commit()

        return jsonify({"message": f"Set {product} as supervised"}), 200
    elif 'supervised' in body.keys() and body['supervised'] is False:
        equity.supervised = False
        # db_session.merge(equity)
        db_session.commit()

        return jsonify({"message": f"Unset {product} as supervised"}), 200
    else:
        return jsonify({"message": f"supervised missing from request body"}), 400

    # dimensions = ["open", "close", "high", "low"]

    # kafka_admin = KafkaAdmin(conf=app.config['KAFKA_CONF'])
    # druid = PlotrDruid(druid_host=app.config['DRUID_HOST'])

    # try:
    #     app.logger.info(f"Creating Kafka topic: {product}")
    #     kafka_admin.create_topic(topics=[product])
    # except Exception as e:
    #     app.logger.error(f"Unable to create Kafka topic {product}")
    #     raise e

    # try:
    #     supervisor_spec = build_kafka_supervisor_spec(
    #         app.config['KAFKA_HOSTS'], stream_name=product, dimensions=dimensions)
    #     app.logger.debug("Submitting Kafka supervisor spec to Druid: " + json.dumps(supervisor_spec))
    #     app.logger.debug(type(supervisor_spec))
    #     druid.submit_kafka_supervisor(spec=supervisor_spec)
    #     app.logger.debug(f"Submitted spec for {product}")
    # except Exception as e:
    #     app.logger.error("Unable to submit supervisor spec to Druid overlord")
    #     raise e

    # try:
    #     equity = CryptoProducts.query.filter(
    #         CryptoProducts.product == product).first()
    #     equity.supervised = True
    #     db_session.commit()
    # except Exception as e:
    #     app.logger.error("Unable to commit changes to database")
    #     raise e

    # return {"status": 200, "message": f"Submitted spec for {product}"}
