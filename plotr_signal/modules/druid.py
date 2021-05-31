import json
from pandas.core.frame import DataFrame
from pydruid.client import PyDruid
from pandas import Series

kafka_supervisor_spec = '''
{
  "type": "kafka",
  "dataSchema": {
    "dataSource": {{ kafka_host }},
    "timestampSpec": {
      "column": "timestamp",
      "format": "auto"
    },
    "dimensionsSpec": {
      "dimensions": [],
      "dimensionExclusions": [
        "timestamp",
        "value"
      ]
    },
    "metricsSpec": [
      {
        "name": "count",
        "type": "count"
      },
      {
        "name": "value_sum",
        "fieldName": "value",
        "type": "doubleSum"
      },
      {
        "name": "value_min",
        "fieldName": "value",
        "type": "doubleMin"
      },
      {
        "name": "value_max",
        "fieldName": "value",
        "type": "doubleMax"
      }
    ],
    "granularitySpec": {
      "type": "uniform",
      "segmentGranularity": "HOUR",
      "queryGranularity": "NONE"
    }
  },
  "ioConfig": {
    "topic": "metrics",
    "inputFormat": {
      "type": "json"
    },
    "consumerProperties": {
      "bootstrap.servers": "localhost:9092"
    },
    "taskCount": 1,
    "replicas": 1,
    "taskDuration": "PT1H"
  },
  "tuningConfig": {
    "type": "kafka",
    "maxRowsPerSegment": 5000000
  }
}
'''

class PlotrDruid(PyDruid):
    def __init__(self, druid_host:str, username=None, password=None, proxies=None, **kwargs):
        self.url = druid_host
        self.endpoint = str()
        self.username = username
        self.password = password
        self.proxies = proxies

    def query_dataframe(self, datasource:str, dimensions:list, granularity:str='minute') -> DataFrame:
        self.endpoint = 'druid/v2/'
        query = self.query_builder.subquery()
        return True

    def submit_kafka_supervisor(self, spec:json, schema:json):
        
        return True
