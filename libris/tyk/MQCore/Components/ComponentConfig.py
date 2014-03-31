import pika
import sys
from loadzen.tyk.MQCore.Components.Constants import EXCHANGE_TYPES


class MQQueueConfiguration(object):
    """
    A queue configuration (used as part of main configuration class below)
    """

    def __init__(self, queue='', durable=False, exclusive=False, auto_delete=False, no_wait=False, arguments=None, exchange="", exchange_type=EXCHANGE_TYPES.DIRECT, routing_key=''):
        self.QUEUE = queue
        self.DURABLE = durable
        self.EXCLUSIVE = exclusive
        self.AUTO_DELETE = auto_delete
        self.NO_WAIT = no_wait
        self.ARGUMENTS = arguments
        self.EXCHANGE = exchange
        self.EXCHANGE_TYPE = exchange_type
        self.ROUTING_KEY = routing_key


class MQConfiguration(object):
    """
        A full configuration for Rabbit
    """
    def __init__(self,
                 connection_type = 'SELECT',
                 host = 'localhost',
                 port = 5672,
                 vhost = '/',
                 username='guest',
                 password='guest'):


        self.SERVER_URL = 'amqp://guest:guest@localhost:5672/'
        self.CONNECTION_TYPE = connection_type
        self.HOST = host
        self.PORT = port
        self.VHOST = vhost
        self.UNAME = username
        self.PWORD = password

    @property
    def ConnectionParameters(self):
        cred = pika.PlainCredentials(self.UNAME, self.PWORD)
        param = pika.ConnectionParameters(
            host=self.HOST,
            port=self.PORT,
            virtual_host=self.VHOST,
            credentials=cred
        )

        return param