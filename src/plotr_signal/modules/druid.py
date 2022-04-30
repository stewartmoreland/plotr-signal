import json
from pandas.core.frame import DataFrame
from pydruid.client import PyDruid
from pandas import Series

from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlencode


class PlotrDruid(PyDruid):
    def __init__(self, druid_host: str, username=None, password=None, proxies=None, **kwargs):
        self.url = druid_host
        self.endpoint = str()
        self.username = username
        self.password = password
        self.proxies = proxies

    def query_dataframe(self, datasource: str, dimensions: list, granularity: str = 'minute') -> DataFrame:
        self.endpoint = 'druid/v2/'
        query = self.query_builder.subquery()
        return True

    def submit_kafka_supervisor(self, spec: dict):
        endpoint = self.url + "/druid/indexer/v1/supervisor"
        headers = {"Content-Type": "application/json"}
        data = urlencode(spec).encode('utf-8')
        request = Request(endpoint, data=data, headers=headers)
        try:
            with urlopen(request) as response:
                response = json.loads(response.read().decode("utf-8"))
                return response
        except HTTPError as e:
            raise e
        except TypeError as e:
            raise e

    def submit_ingestion_task(self, spec: str):
        endpoint = self.url + "/druid/indexer/v1/task"
        data = spec.encode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "Content-Length": len(data)
        }
        request = Request(endpoint, data=data, headers=headers)
        try:
            with urlopen(request) as response:
                response = json.loads(response.read().decode("utf-8"))
                return response
        except HTTPError as e:
            raise e
        except TypeError as e:
            raise e

    def submit_web_socket_stream_kafka_spec(self, stream_name: str):
        wsStreamSpec = [
            {
                "name": "open",
                "type": "floatFirst"
            },
            {
                "name": "close",
                "type": "floatLast"
            },
            {
                "name": "high",
                "type": "floatMax"
            },
            {
                "name": "low",
                "type": "floatMin"
            },
            {
                "name": "volume",
                "type": "floatSum"
            }
        ]

        try:
            spec = build_kafka_supervisor_spec(
                kafka_host=self.url, stream_name=stream_name, metricsSpec=wsStreamSpec)
            self.submit_kafka_supervisor(spec=spec)
        except HTTPError as e:
            raise e
        except Exception as e:
            raise e


def build_kafka_supervisor_spec(kafka_host: str, stream_name: str, dimensions: list = [], metrics_spec: list = [], kafka_port: str = 9092) -> dict:
    kafka_supervisor_spec = {
        "type": "kafka",
        "dataSchema": {
            "dataSource": kafka_host,
            "timestampSpec": {
                "column": "timestamp",
                "format": "auto"
            },
            "dimensionsSpec": {
                "dimensions": dimensions,
                "dimensionExclusions": []
            },
            "metricsSpec": metrics_spec,
            "granularitySpec": {
                "type": "uniform",
                "segmentGranularity": "MINUTE",
                "queryGranularity": "NONE"
            }
        },
        "ioConfig": {
            "topic": stream_name,
            "inputFormat": {
                "type": "json"
            },
            "consumerProperties": {
                "bootstrap.servers": f"{kafka_host}:{kafka_port}"
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

    return kafka_supervisor_spec


def build_task_ingestion_spec(product: str, data, timstamp_column: str = "time") -> dict:
    from datetime import datetime
    now = datetime.now()
    now_str = now.strftime('%Y%m%dT%H%M%S%f')

    task_ingestion_spec = {
        "type": "index_parallel",
        "spec": {
            "dataSchema": {
                "dataSource": product,
                "timestampSpec": {
                    "column": timstamp_column,
                    "format": "iso"
                },
                "dimensionsSpec": {
                    "dimensions": [
                        {"type": "float", "name": "open"},
                        {"type": "float", "name": "close"},
                        {"type": "float", "name": "high"},
                        {"type": "float", "name": "low"},
                        {"type": "float", "name": "price"},
                        {"type": "float", "name": "volume"}
                    ]
                }
            },
            "ioConfig": {
                "type": "index_parallel",
                "inputSource": {
                    "type": "inline",
                    "data": ("\n").join(json.dumps(record) for record in data)
                },
                "inputFormat": {
                    "type": "json"
                },
                "appendToExisting": True
            },
            "tuningConfig": {
                "type": "index_parallel",
                "maxNumConcurrentSubTasks": 2
            }
        }
    }

    return task_ingestion_spec


class CustomJSONEncoder(json.JSONEncoder):
    def _encode(self, obj):
        from datetime import datetime
        if isinstance(obj, dict):
            def transform_date(o):
                return self._encode(o.isoformat() if isinstance(o, datetime) else o)
            return {transform_date(k): transform_date(v) for k, v in obj.items()}
        else:
            return obj

    def encode(self, obj):
        return super(CustomJSONEncoder, self).encode(self._encode(obj))

    def default(self, obj):
        from pandas._libs.tslibs import Timestamp
        from datetime import datetime, date
        try:
            if isinstance(obj, datetime):
                return obj.strftime("%Y-%m-%dT%H:%M:%S.%f")
            elif isinstance(obj, date):
                return obj.strftime("%Y-%m-%d")
            elif isinstance(obj, Timestamp):
                return obj.strftime("%Y-%m-%dT%H:%M:%S.%f")
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return json.JSONEncoder.default(self, obj)
