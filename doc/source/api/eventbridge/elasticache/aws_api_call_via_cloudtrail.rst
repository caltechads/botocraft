.. _api__eventbridge__elasticache__aws_api_call_via_cloudtrail:

ElastiCache: AWS API Call via CloudTrail
========================================

This represents an ElastiCache API call delivered to EventBridge via CloudTrail.
See `AWS documentation
<https://docs.aws.amazon.com/eventbridge/latest/ref/events-ref-elasticache.html>`_
for the event-pattern contract.

Use :meth:`~botocraft.eventbridge.common.CloudTrailApiCallMixin.parsed_request`
for best-effort botocore-backed typing of ``detail.requestParameters``. CloudTrail
may omit or redact fields relative to the live API.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.elasticache.ElastiCacheAWSAPICallViaCloudTrailEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models
----------------

.. automodule:: botocraft.eventbridge.raw.elasticache.aws_api_call_via_cloudtrail
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump
