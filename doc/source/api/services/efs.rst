

EFS (efs)
=========


Primary Models
--------------

Primary models are models that you can act on directly. They are the models that
represent resources in the AWS service, and are acted on by the managers.



.. autopydantic_model:: botocraft.services.efs.AccessPoint
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.FileSystem
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.MountTarget
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.ReplicationConfiguration
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python



Managers
--------

Managers work with the primary models to provide a high-level interface to the
AWS service. They are responsible for creating, updating, and deleting the
resources in the service, as well as any additional operations that are
available for those models.


.. autoclass:: botocraft.services.efs.AccessPointManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.efs.FileSystemManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.efs.MountTargetManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.efs.ReplicationConfigurationManager
   :members:
   :show-inheritance:




Secondary Models
----------------

Secondary models are models that are used by the primary models to organize
their data. They are not acted on directly, but are used to describe the
structure of the fields in the primary models or other secondary models.



.. autopydantic_model:: botocraft.services.efs.DestinationToCreate
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.EFSBackupPolicy
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.EFSCreationInfo
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.EFSDestination
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.EFSPosixUser
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.EFSRootDirectory
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.FileSystemPolicyDescription
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.FileSystemProtectionDescription
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.FileSystemSize
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.LifecycleConfigurationDescription
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.LifecyclePolicy
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python



Request/Response Models
-----------------------

Request/response models are models that are used to describe the structure of
the data that is sent to and received from the AWS service. They are used by
the managers to send requests to the service and to parse the responses that
are received.

You will not often use them directly -- typically they are used by the managers
internally to send requests and parse responses -- but they are included here
for completeness, and because occasionally we return them directly to you
because they have some useful additional information.



.. autopydantic_model:: botocraft.services.efs.BackupPolicyDescription
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.DescribeAccessPointsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.DescribeFileSystemsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.DescribeMountTargetsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.efs.DescribeReplicationConfigurationsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


