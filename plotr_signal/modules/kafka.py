from confluent_kafka import SerializingProducer, DeserializingConsumer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaError

import certifi
from datetime import datetime


class KafkaProducer(object):
    def __init__(self, conf):
        self.conf = conf
        self.producer = SerializingProducer(conf=self.conf)
        self.admin = KafkaAdmin(self.conf)

    def write_msg(self, topic, msg, timestamp):
        self.admin.create_topic(topics=[topic])
        epoch = timestamp_to_epoch(timestamp)
        self.producer.produce(topic=topic, value=msg, timestamp=epoch)


class KafkaConsumer(object):
    def __init__(self, conf):
        self.conf = conf
        self.consumer = DeserializingConsumer(conf=self.conf)


class KafkaAdmin(object):
    def __init__(self, conf:dict):
        self.admin = AdminClient(self.pop_schema_registry_params_from_config(conf))

    @staticmethod
    def pop_schema_registry_params_from_config(conf:dict):
        """Remove potential Schema Registry related configurations from dictionary"""
        conf.pop('schema.registry.url', None)
        conf.pop('basic.auth.user.info', None)
        conf.pop('basic.auth.credentials.source', None)
        return conf

    def create_topic(self, topics:list, partitions:int=3, replication_factor:int=1):
        """
            Create a topic if needed
        """

        new_topics = [NewTopic(topic, num_partitions=partitions, replication_factor=replication_factor) for topic in topics]

        request = self.admin.create_topics(new_topics)
        for topic, f in request.items():
            try:
                f.result()
                print(f"Topic {topic} created")
            except Exception as e:
                if e.args[0].code() != KafkaError.TOPIC_ALREADY_EXISTS:
                    raise "Failed to create topic {}: {}".format(topic, e)

        return list(request.items())


def read_config(config_file):
    """Read configuration for librdkafka clients"""
    conf = {}
    with open(config_file) as fh:
        for line in fh:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split('=', 1)
                conf[parameter] = value.strip()
    conf['ssl.ca.location'] = certifi.where()
    return conf

def timestamp_to_epoch(timestamp, pattern='%d.%m.%Y %H:%M:%S', unit='ms'):
    import time
    return int(time.mktime(time.strptime(timestamp, pattern)))
