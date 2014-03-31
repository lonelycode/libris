from loadzen.settings.log_config import *
from loadzen.settings.tyk_config import tyk_log_level
logger = logging.getLogger("TYK")
logger.level = tyk_log_level
from loadzen.settings.tyk_config import tyk_publish_properties


class QueueBase(object):
    def __init__(self, queue_config, channel=None, connection=None):
        """
        A self-contained queue action for use as part of a component, will bind the queue config to an input channel
        and start consuming.

        :param queue_config: The MQQueueConfiguration object that defines the Exchange and queue to bind to
        :param channel: The input channel object that has been passed in by the component, multiple queue actions can share a channel
        :return:
        """
        self.channel = channel
        self.connection = connection
        self.configuration = queue_config
        self._stopping = False
        self.parent_component = None

    def do_bind(self):
        logger.info("Starting bind for QueueAction: %s" % self.configuration.QUEUE)
        self.setup_exchange(self.configuration.EXCHANGE)

    def setup_exchange(self, exchange_name):
        """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.

        :param str|unicode exchange_name: The name of the exchange to declare

        """
        logger.info('Declaring exchange %s', exchange_name)
        self.channel.exchange_declare(self.on_exchange_declareok,
                                      exchange_name,
                                      exchange_type=self.configuration.EXCHANGE_TYPE,
                                      durable=self.configuration.DURABLE,
                                      passive=False,
                                      auto_delete=self.configuration.AUTO_DELETE,
                                      internal=False,
                                      nowait=self.configuration.NO_WAIT,
                                      arguments=self.configuration.ARGUMENTS,
                                      type=None
                                      )

    def on_exchange_declareok(self, unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

        """
        logger.info('Exchange declared')
        self.setup_queue(self.configuration.QUEUE)

    def setup_queue(self, queue_name):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        logger.info('Declaring queue %s', queue_name)

        self.channel.queue_declare(
            self.on_queue_declareok,
            self.configuration.QUEUE,
            durable = self.configuration.DURABLE,
            exclusive = self.configuration.EXCLUSIVE,
            auto_delete = self.configuration.AUTO_DELETE,
            nowait = self.configuration.NO_WAIT,
            arguments = self.configuration.ARGUMENTS
        )

    def on_queue_declareok(self, method_frame):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method method_frame: The Queue.DeclareOk frame

        """

        logger.info('Binding %s to %s with %s',
            self.configuration.EXCHANGE, self.configuration.QUEUE, self.configuration.ROUTING_KEY)
        self.channel.queue_bind(self.on_bindok, self.configuration.QUEUE,
            self.configuration.EXCHANGE, self.configuration.ROUTING_KEY)

    def deserialise(self, content_type, msg):
        """
        Deserialises a message based on the content type, currently support msgpack and json

        :param string content_type: string representation of the content type
        :param string msg: The return message from Pika
        :return: Message object
        """

        if content_type == 'application/json':
            import simplejson
            return simplejson.loads(msg)

        if content_type == 'application/x-msgpack':
            import msgpack
            return msgpack.unpackb(msg, use_list=True)

    def serialise(self, content_type, msg):
        """
        Derialises a message for sending over the channel

        :param string content_type:  string representation of the content type
        :param msg: the message to encode
        :return: A string object that is encoded appropriately according to content type.
        """

        try:

            if content_type == 'application/json':
                import simplejson
                return simplejson.dumps(msg)

            if content_type == 'application/x-msgpack':
                import msgpack
                return msgpack.packb(msg)
        except Exception, e:
            logger.error('Unable to decode message: %s' % str(e))
            return ""

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        logger.info('Closing connection')
        self.connection.close()

    def on_bindok(self, unused_frame):
        """Override this class to set actions after bind"""


class QueueInputAction(QueueBase):
    def __init__(self, queue_config, channel=None, output_queues={}):
        """
        A QueueAction that acts as a consumer, it takes a MQQueueConfiguration object and will consume objects from the
        defined queue, override the on_message_Callback function to react to icomming messages

        :param queue_config: the MQQueueConfiguration object that tells us what queue to listen in on
        :param channel: the channel object of the connection
        :param output_queues: QueueOutputAction objects that can be used to publish messages out again
        :return: None
        """

        self.output_queues = output_queues
        self._consumer_tag = ''

        super(QueueInputAction, self).__init__(queue_config, channel)

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        logger.info('Adding consumer cancellation callback')
        self.channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        logger.info('Consumer was cancelled remotely, shutting down: %r',
            method_frame)
        self.channel.close()

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        logger.info('Acknowledging message %s', delivery_tag)
        self.channel.basic_ack(delivery_tag)

    def start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """

        logger.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self.channel.basic_consume(self.on_message,
            self.configuration.QUEUE)

    def on_bindok(self, unused_frame):
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        :param pika.frame.Method unused_frame: The Queue.BindOk response frame

        """
        logger.info('Queue bound')
        self.parent_component.register_input_queue_ready(queue=self)
        self.start_consuming()

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
        self.channel.basic_cancel(consumer_tag=self._consumer_tag)

    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel unusedinput_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param str|unicode body: The message body

        """

        unpacked = self.deserialise(properties.content_type, body)
        logger.info('Received message # %s from %s: %s',
            basic_deliver.delivery_tag, properties.app_id, unpacked)

        self.on_message_callback(unused_channel, basic_deliver, properties, unpacked)
        self.acknowledge_message(basic_deliver.delivery_tag)

    def on_cancelok(self, unused_frame):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the connection
        which will automatically close the channel if it's open.

        :param pika.frame.Method unused_frame: The Basic.CancelOk frame

        """
        logger.info('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_connection()

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
        self.channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_message_callback(self, unused_channel, basic_deliver, properties, body):
        """
        Override this method to perform queue actions
        """

class QueueOutputAction(QueueBase):
    def __init__(self, queue_config, channel=None):
        """

        A Queue Action object that will act as a publisher.

        Override the ready() function if you want to configure a looping publisher or active publisher
        use the publish_message() method to publish a message to the channel

        :param queue_config: The queue configuration for the publisher
        :param channel: The 'write' mode channel object
        :return: None
        """

        self._consumer_tag = ''
        self._message_number = 0
        self._deliveries = []
        self.is_ready = False

        super(QueueOutputAction, self).__init__(queue_config, channel)

    def on_bindok(self, unused_frame):
        """This method is invoked by pika when it receives the Queue.BindOk
        response from RabbitMQ. Since we know we're now setup and bound, it's
        time to start publishing."""

        logger.info('Queue bound')
        self.queue_ready()

    def queue_ready(self):
        self.is_ready = True
        self.parent_component.register_output_queue_ready(queue=self)
        self.ready()

    def ready(self):
        pass

    def publish_message(self, message, message_properties=tyk_publish_properties, routing_key_override=None):
        if self._stopping:
            return True

        routing_key = self.configuration.ROUTING_KEY
        if routing_key_override:
            routing_key = routing_key_override

        if self.is_ready:
            to_send = self.serialise(message_properties.content_type, message)

            self.channel.basic_publish(self.configuration.EXCHANGE, routing_key,
                to_send, message_properties)
            self._message_number += 1
            self._deliveries.append(self._message_number)
            logger.info('Published message # %i', self._message_number)
            return True
        else:
            logger.error('Output queue is not ready yet!')
            return False