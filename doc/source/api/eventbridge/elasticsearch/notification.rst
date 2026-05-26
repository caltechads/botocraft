.. _api__eventbridge__elasticsearch__notification:

Elasticsearch Notification
==========================

This is emitted for `Amazon OpenSearch Service Notification` events documented
by AWS, including cluster advisories such as node retirement and domain
isolation notifications.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.elasticsearch.ElasticsearchNotificationEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models from AWS Documentation
---------------------------------------

.. automodule:: botocraft.eventbridge.raw.elasticsearch.notification
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump
