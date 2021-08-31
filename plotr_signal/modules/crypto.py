from pandas import DataFrame, to_datetime
from datetime import date, datetime, timedelta

from plotr_signal.modules import cbpro


def get_crypto_price_history(product: str, start: datetime, end: datetime, interval=60, delta: timedelta = timedelta(minutes=300)) -> DataFrame:
    public_client = cbpro.PublicClient()
    results = []
    try:
        while start < end:
            end_datetime = start + delta
            results.extend(public_client.get_product_historic_rates(
                product_id=product, start=start, end=end_datetime, granularity=interval))
            start = start + delta
    except Exception as e:
        raise e

    df = DataFrame(data=results, columns=[
                   'time', 'low', 'high', 'open', 'close', 'volume'])
    df['time'] = to_datetime(df['time'], unit='s')
    df.set_index(df['time'], drop=True, inplace=True)
    for column in ['low', 'high', 'open', 'close', 'volume']:
        df[column] = df[column].astype(float)

    df['price'] = df[['low', 'high', 'open', 'close']].mean(axis=1)

    return df
