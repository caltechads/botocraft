.. _api__eventbridge__acm__rotated:

ACM Certificate Rotated
=======================

AWS documents this event in the EventBridge service reference but does not
publish a schema-library entry; the raw model is derived from the documented
empty ``detail`` object.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.acm.ACMCertificateRotatedEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models from AWS Documentation
-------------------------------------

.. automodule:: botocraft.eventbridge.raw.acm.acmcertificaterotated
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump
