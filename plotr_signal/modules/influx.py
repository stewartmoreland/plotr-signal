from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from flask import current_app as app
import json

class Influx(object):
    def __init__(self, host=app.config['INFLUXDB_V2_URL'], token=app.config['INFLUXDB_V2_TOKEN']):
        self.client = InfluxDBClient(url=host, token=token, org=app.config['INFLUXDB_V2_ORG'])
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

    def write_price_data(self, price:Point, bucket:str):
        if self.client.buckets_api().find_bucket_by_name(bucket) is None:
            org = self.client.organizations_api().find_organizations()
            app.logger.info(org)
            description = f'time series pricing data for {bucket} securities'
            self.client.buckets_api().create_bucket(bucket_name=bucket, retention_rules=None, description=description, org_id='80b7ba722d23386f')
        
        self.write_api.write(bucket=bucket, record=price)
