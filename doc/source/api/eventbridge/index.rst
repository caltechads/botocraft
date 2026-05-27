.. _overview__events:

EventBridge and SQS Events
==========================

This section groups Botocraft's typed EventBridge wrappers by AWS service so
you can browse from service area to specific event family.

Event Factories
---------------

.. autoclass:: botocraft.eventbridge.factory.EventFactory
    :show-inheritance:


.. autoclass:: botocraft.eventbridge.factory.AbstractEventFactory
    :show-inheritance:

Events
------

.. autoclass:: botocraft.eventbridge.EventBridgeEvent
    :show-inheritance:

Botocraft-provided events
^^^^^^^^^^^^^^^^^^^^^^^^^

Browse supported EventBridge wrappers by AWS service:

.. toctree::
   :maxdepth: 1

   acm/index
   codepipeline/index
   ecr/index
   elasticsearch/index
   elbv2/index
   ecs/index
   opensearch/index
   ssm/index
