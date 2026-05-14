.. _api__eventbridge__ssm__opsitem_create:

SSM OpsItem Create
==================

This is emitted when Systems Manager sends a `OpsItem Create` event. See `AWS
documentation
<https://docs.aws.amazon.com/systems-manager/latest/userguide/monitoring-systems-manager-event-examples.html>`_
for example payloads and event behavior.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.ssm.SSMOpsItemCreateEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models from AWS Example Payload
-----------------------------------------

.. automodule:: botocraft.eventbridge.raw.ssm.opsitem_create
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump
