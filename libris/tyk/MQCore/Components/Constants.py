import pika


class EXCHANGE_TYPES(object):
    DIRECT = 'direct'
    FANOUT = 'fanout'
    TOPIC = 'topic'


class CONNECTION_TYPES(object):
    SELECT = pika.SelectConnection
    TORNADO = pika.adapters.tornado_connection.TornadoConnection
    BLOCKING = pika.BlockingConnection