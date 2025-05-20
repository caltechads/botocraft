.. _overview__events:

Everbridge and SQS Events
=========================

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

Botocraft provided events
^^^^^^^^^^^^^^^^^^^^^^^^^

ECR
    * :doc:`/api/eventbridge/ecr/aws_api_call_via_cloudtrail`
    * :doc:`/api/eventbridge/ecr/ecr_image_action`
    * :doc:`/api/eventbridge/ecr/ecr_scan_action`
    * :doc:`/api/eventbridge/ecr/pull_through_cache_action`
    * :doc:`/api/eventbridge/ecr/referrer_action`
    * :doc:`/api/eventbridge/ecr/replication_action`
    * :doc:`/api/eventbridge/ecr/scan_resource_change`

ECS
    * :doc:`/api/eventbridge/ecs/aws_api_call_via_cloudtrail`
    * :doc:`/api/eventbridge/ecs/container_instance_change`
    * :doc:`/api/eventbridge/ecs/service_action`
    * :doc:`/api/eventbridge/ecs/service_deployment_state_change`
    * :doc:`/api/eventbridge/ecs/task_state_change`