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

SSM
    * :doc:`/api/eventbridge/ssm/calendar_state_change`
    * :doc:`/api/eventbridge/ssm/change_request_status_update`
    * :doc:`/api/eventbridge/ssm/configuration_compliance_state_change`
    * :doc:`/api/eventbridge/ssm/ec2_automation_execution_status_change_notification`
    * :doc:`/api/eventbridge/ssm/ec2_automation_step_status_change_notification`
    * :doc:`/api/eventbridge/ssm/ec2_command_invocation_status_change_notification`
    * :doc:`/api/eventbridge/ssm/ec2_command_status_change_notification`
    * :doc:`/api/eventbridge/ssm/ec2_state_manager_association_state_change`
    * :doc:`/api/eventbridge/ssm/ec2_state_manager_instance_association_state_change`
    * :doc:`/api/eventbridge/ssm/maintenance_window_execution_state_change_notification`
    * :doc:`/api/eventbridge/ssm/maintenance_window_state_change_notification`
    * :doc:`/api/eventbridge/ssm/maintenance_window_target_registration_notification`
    * :doc:`/api/eventbridge/ssm/maintenance_window_task_execution_state_change_notification`
    * :doc:`/api/eventbridge/ssm/maintenance_window_task_target_invocation_state_change_notification`
    * :doc:`/api/eventbridge/ssm/opsitem_create`
    * :doc:`/api/eventbridge/ssm/opsitem_update`
    * :doc:`/api/eventbridge/ssm/parameter_store_change`