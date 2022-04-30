from celery import Celery
from flask import current_app as app
from plotr_signal.modules.cbpro import public_client
from pandas import DataFrame, to_datetime
from datetime import datetime, timedelta

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task()
def get_crypto_price_history(product:str, start:datetime, end:datetime, interval=60, delta:timedelta=timedelta(minutes=300)) -> DataFrame:
    results = []
    current_dt = start
    while start < end:
        end_datetime = current_dt + delta
        results.extend(public_client.get_product_historic_rates(
            product_id=product, start=current_dt, end=end_datetime, granularity=interval))
        current_dt = current_dt + delta

    df = DataFrame(data=results, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
    df['time'] = to_datetime(df['time'], unit='s')
    df.set_index(df['time'], drop=True, inplace=True)
    for column in ['low', 'high', 'open', 'close', 'volume']:
        df[column] = df[column].astype(float)

    df['price'] = df[['low', 'high', 'open', 'close']].mean(axis=1)

    return df
