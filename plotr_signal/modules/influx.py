from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS

from pandas import DataFrame

from flask import current_app as app
import json

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
            self.client.buckets_api().create_bucket(bucket_name=bucket, retention_rules=None, description=description, org_id='80b7ba722d23386f')
        
        self.write_api.write(bucket=bucket, record=price)

    def write_dataframe(self, dataframe:DataFrame=None, bucket:str=None):
        if self.client.buckets_api().find_bucket_by_name(bucket) is None:
            description = f'time series pricing data for {bucket} securities'
            self.client.buckets_api().create_bucket(bucket_name=bucket, retention_rules=None, description=description, org_id='80b7ba722d23386f')

        self.write_api.write(record=dataframe, bucket=bucket, data_frame_measurement_name='price', data_frame_tag_columns=[
                                                                                            "open_price",
                                                                                            "close_price",
                                                                                            "low_price",
                                                                                            "high_price",
                                                                                            "total_volume_of_all_trades",
                                                                                            "transactions",
                                                                                            "timestamp_of_this_aggregation"
                                                                                        ])
