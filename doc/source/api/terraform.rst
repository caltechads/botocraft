.. _api__terraform:

Terraform reference
===================

Global resources
----------------

These resources get created in the ``terraform/common`` directory.  These
resources are workspace independent.

.. tf:resource:: aws_ecr_repository.repo
    :rootmodule: common

.. tf:resource:: aws_elasticsearch_domain.es
    :rootmodule: common

.. tf:module:: build-pipeline
    :rootmodule: common

Outputs
^^^^^^^

.. tf:output:: ecr_repository_url
    :rootmodule: common

.. tf:output:: elasticsearch_domain_endpoint
    :rootmodule: common


Per workspace resources
-----------------------

These resources get created in the ``terraform/app`` directory.  These resources
get created for each new workspace created via ``terraform workspace new
<workspace>``.

.. tf:module:: storage-bucket
    :rootmodule: app

.. tf:module:: storage-bucket-policies
    :rootmodule: app

.. tf:resource:: aws_s3_bucket_cors_configuration.storage-bucket
    :rootmodule: app

.. tf:module:: service
    :rootmodule: app

.. tf:resource:: aws_cloudwatch_query_definition.all
    :rootmodule: app

.. tf:module:: api_target_group
    :rootmodule: app

.. tf:resource:: aws_route53_record.api
    :rootmodule: app

Outputs
^^^^^^^

.. tf:output:: ecr_repository_url
    :rootmodule: app

.. tf:output:: s3_bucket_name
    :rootmodule: app

.. tf:output:: s3_bucket_arn
    :rootmodule: app

.. tf:output:: app_target_group_arn
    :rootmodule: app

.. tf:output:: api_target_group_arn
    :rootmodule: app

.. tf:output:: cluster_name
    :rootmodule: app

.. tf:output:: task_role_arn
    :rootmodule: app

.. tf:output:: task_execution_role_arn
    :rootmodule: app

.. tf:output:: kms_key_arn
    :rootmodule: app

.. tf:output:: subnets
    :rootmodule: app

.. tf:output:: security_groups
    :rootmodule: app

.. tf:output:: rds_address
    :rootmodule: app

.. tf:output:: rds_port
    :rootmodule: app

.. tf:output:: redis_endpoint
    :rootmodule: app

.. tf:output:: elasticsearch_domain_endpoint
    :rootmodule: app