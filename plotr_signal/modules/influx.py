from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS, SYNCHRONOUS

from pandas import DataFrame

from flask import current_app as app

class Influx(object):
    def __init__(self, host=app.config['INFLUXDB_V2_URL'], token=app.config['INFLUXDB_V2_TOKEN']):
        self.client = InfluxDBClient(url=host, token=token, org=app.config['INFLUXDB_V2_ORG'])
        # self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
        self.write_api = self.client.write_api(write_options=WriteOptions(batch_size=500,
                                                                          flush_interval=10_000,
                                                                          jitter_interval=2_000,
                                                                          retry_interval=5_000,
                                                                          max_retries=5,
                                                                          max_retry_delay=30_000,
                                                                          exponential_base=2))
        self.query_api = self.client.query_api()

    def write_point_data(self, price:Point, bucket:str):
        if self.client.buckets_api().find_bucket_by_name(bucket) is None:
            org = self.client.organizations_api().find_organizations()
            app.logger.info(org)
            description = f'time series pricing data for {bucket} securities'
            self.client.buckets_api().create_bucket(bucket_name=bucket, retention_rules=None, description=description, org_id=app.config['INFLUXDB_V2_ORG_ID'])
        
        self.write_api.write(bucket=bucket, record=price)

    def write_dataframe(self, dataframe:DataFrame=None, bucket:str=None, measurement:str=None):
        if self.client.buckets_api().find_bucket_by_name(bucket) is None:
            description = f'time series pricing data for {bucket} securities'
            self.client.buckets_api().create_bucket(bucket_name=bucket, retention_rules=None, description=description, org_id=app.config['INFLUXDB_V2_ORG_ID'])

        self.write_api.write(record=dataframe, bucket=bucket, data_frame_measurement_name=measurement)

    def get_equity_field_dataframe(self, symbol, from_, to, interval:str='1m', field:str='close', index:list=['_time']):
        query = f'''
        from(bucket: "{symbol}")
            |> range(start: {from_}, stop: {to})
            |> filter(fn: (r) => r["_measurement"] == "price")
            |> filter(fn: (r) => r["_field"] == "{field}")
            |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
            |> yield(name: "mean")
        '''

        df = self.query_api.query_data_frame(query=query, data_frame_index=index)

        return df

    def get_aggregate_dataframe(self, symbol, from_, to, interval:str='5m', index=['_time']):
        query = f'''
        from(bucket: {symbol})
            |> range(start: {from_}, stop: {to})
            |> filter(fn: (r) => r["_measurement"] == "price")
            |> filter(fn: (r) => r["_field"] == "high")
            |> aggregateWindow(every: {interval}, fn: max, createEmpty: false)
            |> yield(name: "high")

        from(bucket: {symbol})
            |> range(start: {from_}, stop: {to})
            |> filter(fn: (r) => r["_measurement"] == "price")
            |> filter(fn: (r) => r["_field"] == "low")
            |> aggregateWindow(every: {interval}, fn: min, createEmpty: false)
            |> yield(name: "low")

        from(bucket: {symbol})
            |> range(start: {from_}, stop: {to})
            |> filter(fn: (r) => r["_measurement"] == "price")
            |> filter(fn: (r) => r["_field"] == "open")
            |> aggregateWindow(every: {interval}, fn: first, createEmpty: false)
            |> yield(name: "open")

        from(bucket: {symbol})
            |> range(start: {from_}, stop: {to})
            |> filter(fn: (r) => r["_measurement"] == "price")
            |> filter(fn: (r) => r["_field"] == "close")
            |> aggregateWindow(every: {interval}, fn: last, createEmpty: false)
            |> yield(name: "close")
        '''

        df = self.query_api.query_data_frame(query=query, data_frame_index=index)

        return df
