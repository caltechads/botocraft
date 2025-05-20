.. _api__eventbridge__ecs__service_deployment_state_change:


ECS Deployment State Change
===========================

This is emitted when an ECS Service Deployment occurs.  See `AWS
documentation
<https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_service_deployment_events.html>`_
for more information on when this might be emitted.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.ecs.ECSServiceDeploymentStateChangeEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models from AWS Schema
--------------------------------

.. automodule:: botocraft.eventbridge.ecs.raw.service_deployment_state_change
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump