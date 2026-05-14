.. _overview__eventbridge_events:

EventBridge and SQS events
==========================

Events in botocraft
-------------------

``botocraft`` ships typed EventBridge event wrappers under
``botocraft.eventbridge``.  Those wrappers sit on top of raw Pydantic models
generated from EventBridge schemas and add Botocraft-specific ergonomics such as
relationships and convenience properties.

At runtime, :py:class:`~botocraft.eventbridge.factory.EventFactory` takes raw
EventBridge JSON and returns one of two things:

* a known :py:class:`~botocraft.eventbridge.EventBridgeEvent` subclass when the
  ``(source, detail-type)`` pair has a registered wrapper
* a raw ``dict`` when the event type is not yet mapped

Two service areas matter here:

* ``botocraft.services.events`` is the EventBridge control plane for buses,
  rules, targets, and event publishing
* ``botocraft.services.schemas`` is the Schema Registry surface used for
  authoring and exporting raw EventBridge schemas

For maintainership docs, see:

* :doc:`/runbook/eventbridge_event_from_schema`
* :doc:`/runbook/eventbridge_event_from_example`

Receiving EventBridge events from SQS
-------------------------------------

:py:meth:`~botocraft.services.sqs.Queue.receive` and
:py:meth:`~botocraft.services.sqs.Queue.poll` return
:py:class:`~botocraft.services.sqs.Message` objects.

That detail matters: ``Queue.poll()`` does **not** yield parsed events
directly.  Instead, each ``Message`` exposes an ``event`` property that runs the
message body through the configured event factory.

.. code-block:: python

    from botocraft.services import Queue

    queue = Queue.objects.get("botocraft-demo-events")

    for message in queue.poll():
        event = message.event

        if isinstance(event, dict):
            print("Unmapped event:", event.get("source"), event.get("detail-type"))
            continue

        print(event.source, event.detail_type)
        print(event.detail)

Use :py:meth:`~botocraft.services.sqs.Queue.receive` when you want one bounded
receive call instead of an infinite poll loop:

.. code-block:: python

    messages = queue.receive(MaxNumberOfMessages=10, WaitTimeSeconds=20)

    for message in messages:
        event = message.event
        print(type(event))

Creating an SQS queue that receives EventBridge events
------------------------------------------------------

Today the most direct flow is:

1. create the queue with Botocraft
2. create the EventBridge rule with Botocraft
3. add the queue policy and target wiring with the underlying AWS clients
4. consume messages from the queue with ``Queue.poll()``

The example below uses the default event bus.  For a custom bus, pass
``EventBusName`` when you create the rule and when you call ``put_targets``.

.. code-block:: python

    import json

    from botocraft.services import EventRule, Queue

    Queue.objects.create(Queue(QueueName="botocraft-demo-events"))
    queue = Queue.objects.get("botocraft-demo-events")

    rule = EventRule(
        Name="botocraft-demo-events",
        EventPattern=json.dumps(
            {
                "source": ["aws.ecs"],
                "detail-type": ["ECS Task State Change"],
            }
        ),
    )
    rule_arn = EventRule.objects.create(rule)

    queue_arn = queue.Attributes["QueueArn"]
    sqs_client = queue.session.client("sqs")
    events_client = queue.session.client("events")

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowEventBridgeSendMessage",
                "Effect": "Allow",
                "Principal": {"Service": "events.amazonaws.com"},
                "Action": "sqs:SendMessage",
                "Resource": queue_arn,
                "Condition": {
                    "ArnEquals": {
                        "aws:SourceArn": rule_arn,
                    }
                },
            }
        ],
    }

    sqs_client.set_queue_attributes(
        QueueUrl=queue.QueueUrl,
        Attributes={"Policy": json.dumps(policy)},
    )

    events_client.put_targets(
        Rule=rule.Name,
        Targets=[
            {
                "Id": "botocraft-demo-queue",
                "Arn": queue_arn,
            }
        ],
    )

Once the rule starts matching events, you can consume them with the same queue
object:

.. code-block:: python

    for message in queue.poll():
        event = message.event

        if isinstance(event, dict):
            print("Unhandled event type:", event.get("detail-type"))
            continue

        print(f"{event.source}: {event.detail_type}")

Using a custom event factory
----------------------------

If you have custom event wrappers, subclass
:py:class:`~botocraft.eventbridge.factory.EventFactory` and extend its
``event_class_map``.

.. code-block:: python

    from botocraft.eventbridge import EventFactory


    class MyEventFactory(EventFactory):
        event_class_map = {
            **EventFactory.event_class_map,
            ("my.custom.source", "Widget Changed"): WidgetChangedEvent,
        }

Then pass that factory into ``receive()`` or ``poll()``:

.. code-block:: python

    for message in queue.poll(EventFactoryClass=MyEventFactory):
        event = message.event
        print(type(event))

Authoring new AWS event wrappers
--------------------------------

When you need to add support for another AWS EventBridge event, prefer the new
Schema Registry workflow:

* use ``botocraft.services.schemas`` to inspect registry content
* use ``botocraft eventbridge export-service <service>`` to generate raw models
* add handwritten wrappers in ``botocraft.eventbridge.<service>``
* register them through the module's ``EVENT_CLASS_MAP``

That is the workflow documented in
:doc:`/runbook/eventbridge_event_from_schema`.  If the event exists only as an
example payload in AWS docs, switch to
:doc:`/runbook/eventbridge_event_from_example`.