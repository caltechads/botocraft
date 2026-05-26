.. _api__eventbridge__elasticsearch__software_update_notification:

Elasticsearch Software Update Notification
==========================================

This wrapper covers legacy `Amazon ES Service Software Update Notification`
detail types. AWS documents renamed OpenSearch notifications separately.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.elasticsearch.ElasticsearchSoftwareUpdateNotificationEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models from AWS Documentation
---------------------------------------

.. automodule:: botocraft.eventbridge.raw.elasticsearch.software_update_notification
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump
