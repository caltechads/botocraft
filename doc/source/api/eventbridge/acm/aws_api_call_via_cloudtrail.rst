.. _api__eventbridge__acm__aws_api_call_via_cloudtrail:

ACM: AWS API Call via CloudTrail
================================

This represents an ACM API call delivered to EventBridge via CloudTrail. See
`AWS documentation
<https://docs.aws.amazon.com/eventbridge/latest/ref/events-ref-acm.html>`_ for
the event-pattern contract.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.acm.ACMAWSAPICallViaCloudTrailEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models from AWS Documentation
---------------------------------------

.. automodule:: botocraft.eventbridge.raw.acm.aws_api_call_via_cloudtrail
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump
