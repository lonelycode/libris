import sys
from loadzen.settings.log_config import *
logger = logging.getLogger("LZ-HELPERS")
from docopt import docopt

sys.path.append('/')
sys.path.append('/tyk/Dependencies/mojo-tyk')

from loadzen.tyk.MQCore.Components.Component import BaseComponent
from loadzen.tyk.MQCore.Components.QueueAction import QueueInputAction
from loadzen.tyk.MQCore.Components.ComponentConfig import MQConfiguration, MQQueueConfiguration
from loadzen.tyk.MQCore.Components.Constants import EXCHANGE_TYPES
logging.basicConfig(level=logger.warning)
host_config = MQConfiguration()
input_queue_config = MQQueueConfiguration(exchange_type=EXCHANGE_TYPES.TOPIC, durable=True)
msg_to_send = ''


class ReceiveMessage(QueueInputAction):
    """
    This action will publish a message to the output queue
    """
    def on_message_callback(self, unused_channel, basic_deliver, properties, body):
        print "Message Received: %s" % body

    # def acknowledge_message(self, delivery_tag):
    #     #Stop delivery confirm!
    #     pass

__doc__ = """
Tyk Wiretap
===========

Usage: wiretap.py [-h=<host>] [-p=<port>] [-v=<vhost>] -e=<exchange> -q=<queue> -r=<routing-key>

Options:
    --help               Show this message
    -h=<host>            Host
    -p=<port>            Port
    -v=<vhost>           Vhost
    -e=<exchange>        Exchange
    -q=<queue>           Queue name
    -r=<routing-key>     Routing key
"""


if __name__ == '__main__':
    #Parse the command line options
    arguments = docopt(__doc__, version='Tyk Service Manager v1.0')

    if arguments['-h']:
        host_config.HOST = arguments['-h']
    if arguments['-p']:
        host_config.PORT = arguments['-p']
    if arguments['-v']:
        host_config.VHOST = arguments['-v']
    if arguments['-e']:
        input_queue_config.EXCHANGE = arguments['-e']
    if arguments['-q']:
        input_queue_config.QUEUE = arguments['-q']
    if arguments['-r']:
        input_queue_config.ROUTING_KEY = arguments['-r']


    receiveComponent = BaseComponent(host_config,
        input_queues={'DefaultReceiveMessage': ReceiveMessage(input_queue_config)},
        output_queues={
        })

    receiveComponent.run()