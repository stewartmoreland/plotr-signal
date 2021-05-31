from confluent_kafka import SerializingProducer, DeserializingConsumer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaError


class KafkaProducer(object):
    def __init__(self, host, group_id):
        self.conf = {
            'bootstrap.servers': host,
            'group.id': group_id,
            'session.timeout.ms': 6000,
            'auto.offset.reset': 'earliest'
        }

        self.producer = SerializingProducer(conf=self.conf)


class KafkaConsumer(object):
    def __init__(self, host, group_id):
        self.conf = {
            'bootstrap.servers': host,
            'group.id': group_id,
            'session.timeout.ms': 6000,
            'auto.offset.reset': 'earliest'
        }

        self.consumer = DeserializingConsumer(conf=self.conf)


def read_ccloud_config(config_file):
    """Read Confluent Cloud configuration for librdkafka clients"""

    conf = {}
    with open(config_file) as fh:
        for line in fh:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split('=', 1)
                conf[parameter] = value.strip()

    #conf['ssl.ca.location'] = certifi.where()

    return conf


def pop_schema_registry_params_from_config(conf):
    """Remove potential Schema Registry related configurations from dictionary"""

    conf.pop('schema.registry.url', None)
    conf.pop('basic.auth.user.info', None)
    conf.pop('basic.auth.credentials.source', None)

    return conf


def create_topic(conf, topics):
    """
        Create a topic if needed
        Examples of additional admin API functionality:
        https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/adminapi.py
    """

    admin_client_conf = pop_schema_registry_params_from_config(conf.copy())
    a = AdminClient(admin_client_conf)

    new_topics = [NewTopic(topic, num_partitions=3, replication_factor=1) for topic in topics]

    fs = a.create_topics(topics=new_topics)
    for topic, f in fs.items():
        try:
            f.result()
            return "Topic {} created".format(topic)
        except Exception as e:
            if e.args[0].code() != KafkaError.TOPIC_ALREADY_EXISTS:
                raise "Failed to create topic {}: {}".format(topic, e)

