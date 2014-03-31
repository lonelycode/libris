from loadzen.settings.log_config import *
from loadzen.settings.tyk_config import tyk_log_level
logger = logging.getLogger("TYK")
logger.level = tyk_log_level

class ChannelAction(object):
    def __init__(self, connection, ready_callback=None):
        """Setup the example publisher object, passing in the URL we will use
        to connect to RabbitMQ.

        """
        self._connection = connection
        self._channel = None
        self.ready_callback=ready_callback

        self.open_channel()

    def open_channel(self):
        """This method will open a new channel with RabbitMQ by issuing the
        Channel.Open RPC command. When RabbitMQ confirms the channel is open
        by sending the Channel.OpenOK RPC reply, the on_channel_open method
        will be invoked.

        """
        #print "CHANNEL OPEN"
        logger.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        logger.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, method_frame):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as redeclare an exchange or queue with
        different paramters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.frame.Method method_frame: The Channel.Close method frame

        """
        logger.warning('Channel was closed: (%s) %s',
            method_frame.method.reply_code,
            method_frame.method.reply_text)
        self._connection.close()

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        logger.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.ready()

    def ready(self):
        if self.ready_callback:
            self.ready_callback(self._channel)