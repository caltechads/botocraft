.. _api__eventbridge__ecr__referrer_action:

ECR Image Referrer Action
=========================

This is emitted when an ECR image referrer action occurs.  See `AWS
documentation
<https://docs.aws.amazon.com/AmazonECR/latest/userguide/ecr-eventbridge.html>`_
for more information on when this might be emitted.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.ecr.ECRReferrerActionEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models from AWS Schema
--------------------------------

.. automodule:: botocraft.eventbridge.ecr.raw.ecr_referrer_action
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump