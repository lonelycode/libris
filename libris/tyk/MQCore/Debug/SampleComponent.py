from loadzen.tyk.MQCore.Components.QueueAction import QueueInputAction, QueueOutputAction
from loadzen.tyk.MQCore.Components.Component import BaseComponent
from loadzen.tyk.MQCore.Components.ComponentConfig import MQConfiguration, MQQueueConfiguration
from loadzen.settings.log_config import *
logger = logging.getLogger("TYK")

logging.basicConfig(level=logger.info)

host_config = MQConfiguration()
input_queue_config = MQQueueConfiguration(queue='component-input-test-queue', exchange='component-exchange', routing_key='component-input-test')
output_queue_config = MQQueueConfiguration(queue='component-output-test-queue', exchange='component-exchange', routing_key='component-output-test')
reading_input_queue_config = MQQueueConfiguration(queue='component-output-input-test-queue', exchange='component-exchange', routing_key='component-output-test')


class InputAction(QueueInputAction):
    """
    This action will publish to the TestOutputQueue any messages comming into the TestInputQueue
    """
    def on_message_callback(self, unused_channel, basic_deliver, properties, body):
        print "FORWARDING MESSAGE ON: %s" % body
        self.output_queues['TestOutputQueue'].publish_message(body.upper())


class SelfReceivingInputFunction(QueueInputAction):
    def on_message_callback(self, unused_channel, basic_deliver, properties, body):
        print "This should be CAPITALISED: %s" % body

thisComponent = BaseComponent(
    host_config,
    input_queues={
        'TestInput':InputAction(queue_config=input_queue_config),
        'CheckerInput': SelfReceivingInputFunction(queue_config=reading_input_queue_config)
    },
    output_queues={
        'TestOutputQueue':QueueOutputAction(output_queue_config)
    })

thisComponent.run()