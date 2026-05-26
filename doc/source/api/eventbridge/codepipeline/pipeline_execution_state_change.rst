.. _api__eventbridge__codepipeline__pipeline_execution_state_change:

CodePipeline Pipeline Execution State Change
============================================

This is emitted when a CodePipeline pipeline execution changes state. See `AWS
documentation
<https://docs.aws.amazon.com/codepipeline/latest/userguide/detect-state-changes-cloudwatch-events.html>`_
for more information on when this might be emitted.


Primary Model
-------------

.. autopydantic_model:: botocraft.eventbridge.codepipeline.CodePipelinePipelineExecutionStateChangeEvent
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump


Raw Event Models from AWS Schema
--------------------------------

.. automodule:: botocraft.eventbridge.raw.codepipeline.codepipelinepipelineexecutionstatechange
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump
