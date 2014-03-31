import sys
sys.path.append('/')
sys.path.append('/tyk/Dependencies/mojo-tyk')

from loadzen.settings.log_config import *
from loadzen.settings.tyk_config import tyk_log_level
logger = logging.getLogger("TYK")
logger.level = tyk_log_level
from loadzen.tyk.MQCore.Components.Constants import CONNECTION_TYPES
from ChannelAction import ChannelAction
from signal import signal, SIGTERM


class BaseComponent(object):
    def __init__(self, host_config, input_queues={}, output_queues={}):
        """Setup the example publisher object, passing in the URL we will use
        to connect to RabbitMQ.

        """
        self._connection = None
        self._configuration = host_config
        self._input_channel = None
        self._output_channel = None
        self._closing_queues = 0
        self.input_queues = input_queues
        self.output_queues = output_queues
        self.guid = ''
        self.component_meta = {}
        self.arguments = {}
        self.ready_input_queues = 0
        self.ready_output_queues = 0
        self.out_callback_queue = {}
        self.in_callback_queue = {}

    def register_callback_on_out_queue(self, queue_id, callback):
        if queue_id in self.out_callback_queue.keys():
            self.out_callback_queue[queue_id].append(callback)
        else:
            self.out_callback_queue[queue_id] = [callback]

    def register_callback_on_in_queue(self, queue_id, callback):
        if queue_id in self.in_callback_queue.keys():
            self.in_callback_queue[queue_id].append(callback)
        else:
            self.in_callback_queue[queue_id] = [callback]

    def register_input_queue_ready(self, queue=None):
        # self.ready_input_queues += 1
        # logger.info('Registered ready IN queues: %s / %s' % (str(self.ready_input_queues), str(len(self.input_queues))))
        # if self.ready_input_queues == len(self.input_queues):
        logger.info("Running callbacks in register for queue")
        if queue:
            if queue.configuration.QUEUE in self.in_callback_queue.keys():
                logger.info("Running queued actions for: %s" % str(queue.configuration.QUEUE))
                for callback in self.in_callback_queue[queue.configuration.QUEUE]:
                    callback()

                del self.out_callback_queue[queue.configuration.QUEUE]

            self.input_queues_ready()

    def register_output_queue_ready(self, queue=None):
        # self.ready_output_queues += 1
        # logger.info('Registered ready OUT queues: %s / %s' % (str(self.ready_output_queues), str(len(self.output_queues))))
        # if self.ready_output_queues == len(self.output_queues):
        logger.info("Running callbacks in register for queue")
        if queue:
            if queue.configuration.QUEUE in self.out_callback_queue.keys():
                logger.info("Running queued actions for: %s" % str(queue.configuration.QUEUE))
                for callback in self.out_callback_queue[queue.configuration.QUEUE]:
                    callback()

                del self.out_callback_queue[queue.configuration.QUEUE]

            self.output_queues_ready()

    def input_queues_ready(self):
        pass

    def output_queues_ready(self):
        pass

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.
        """

        logger.info('Connecting to %s using %s as Connection Type',
                     self._configuration.HOST,
                     self._configuration.CONNECTION_TYPE)

        if self._configuration.CONNECTION_TYPE == 'SELECT':
            self._connection = CONNECTION_TYPES.SELECT(
                self._configuration.ConnectionParameters,
                self.on_connection_open)

            return self._connection

        elif self._configuration.CONNECTION_TYPE == 'TORNADO':
            self._connection =  CONNECTION_TYPES.TORNADO(
                self._configuration.ConnectionParameters,
                self.on_connection_open)

            return self._connection

        elif self._configuration.CONNECTION_TYPE == 'BLOCKING':
            raise TypeError("Using BLOCKING publisher is not supported")

        if self._connection:
            return self._connection
        else:
            return False

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        logger.info('Closing connection')
        self._connection.close()

    def add_on_connection_close_callback(self):
        """This method adds an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.

        """
        logger.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, method_frame):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.frame.Method method_frame: The method frame from RabbitMQ

        """
        logger.warning('Server closed connection, reopening: (%s) %s',
                        method_frame.method.reply_code,
                        method_frame.method.reply_text)
        self._channel = None
        self._connection = self.connect()

    def on_connection_open(self, unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :type unused_connection: pika.SelectConnection

        """

        logger.info('Connection opened')
        self.add_on_connection_close_callback()
        self.connection_ready()

    def input_channel_ready(self, channel):
        self._input_channel = channel
        for name, queue in self.input_queues.iteritems():
            self.input_queues[name].channel = self._input_channel
            self.input_queues[name].connection = self._connection
            self.input_queues[name].output_queues = self.output_queues
            self.input_queues[name].parent_component = self
            self.input_queues[name].do_bind()

    def output_channel_ready(self, channel):
        self._output_channel = channel
        for name, queue in self.output_queues.iteritems():
            self.output_queues[name].channel = self._output_channel
            self.output_queues[name].connection = self._connection
            self.output_queues[name].parent_component = self
            self.output_queues[name].do_bind()

    def connection_ready(self):
        # 1. Create input channel
        if self.input_queues:
            logger.info("Creating input channel")
            ChannelAction(self._connection, ready_callback=self.input_channel_ready)
        # 2. Create output channel
        if self.output_queues:
            logger.info("Creating output channels")
            ChannelAction(self._connection, ready_callback=self.output_channel_ready)

    def complete_shutdown(self, unused_frame):
        self._closing_queues += 1

        if self._closing_queues == len(self.input_queues):
            logger.info('All consumers have disconnected successfully, closing down channel and connection')
            self.close_channel()
            self.close_connection()

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        for name, queue in self.input_queues.iteritems():
            logger.info('Sending a Basic.Cancel RPC command to RabbitMQ for: %s' % name)
            self._input_channel.basic_cancel(self.complete_shutdown, self.input_queues[name]._consumer_tag)

        for name, queue in self.output_queues.iteritems():
            logger.info('Sending a Basic.Cancel RPC command to RabbitMQ for: %s' % name)
            self._output_channel.basic_cancel(self.complete_shutdown, self.output_queues[name]._consumer_tag)

    def close_channel(self):
        logger.info("Closing I/O channels")
        try:
            self._input_channel.close()
        except:
            logger.warning('Input channel already closed')
        try:
            self._output_channel.close()
        except:
            logger.warning('Output channel already closed')

    def stop(self, keyboard=False):
        logger.info('Stopping, keyboard interupt: %s' % str(keyboard))
        self._stopping = True

        self.stop_consuming()

        self.close_channel()
        self.close_connection()

        self._connection.ioloop.start()

    def handle_graceful_kill(self, signum, frame):
        #If the process terminates unexpectedly, make sure we're handling it gracefully
        logger.warning('Detected terminate signal... initiating cleanup')
        self.stop()

    def _run(self):
        self._connection = self.connect()

        signal(SIGTERM, self.handle_graceful_kill)

        try:
            # Loop so we can communicate with RabbitMQ
            self._connection.ioloop.start()
        except KeyboardInterrupt:
            # Gracefully close the connection
            self.stop(keyboard=True)

    def run(self):
        """
        Override this function if you need to manage pre-connection configurations
        """

        self._run()
