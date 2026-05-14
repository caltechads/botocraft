.. _api__eventbridge__ssm__calendar_state_change:

SSM Calendar State Change
=========================

This is emitted when a Systems Manager Change Calendar changes state. See `AWS
documentation
<https://docs.aws.amazon.com/systems-manager/latest/userguide/reference-eventbridge-events.html>`_
for more information on when this might be emitted.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.ssm.SSMCalendarStateChangeEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models from AWS Schema
--------------------------------

.. automodule:: botocraft.eventbridge.raw.ssm.calendarstatechange
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump
