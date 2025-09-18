

IAM (iam)
=========


Primary Models
--------------

Primary models are models that you can act on directly. They are the models that
represent resources in the AWS service, and are acted on by the managers.



.. autopydantic_model:: botocraft.services.iam.IAMAccessKey
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMGroup
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMLoginProfile
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMPolicy
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMPolicyVersion
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMRole
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMSSHPublicKey
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMUser
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.InstanceProfile
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python



Managers
--------

Managers work with the primary models to provide a high-level interface to the
AWS service. They are responsible for creating, updating, and deleting the
resources in the service, as well as any additional operations that are
available for those models.


.. autoclass:: botocraft.services.iam.IAMAccessKeyManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.iam.IAMGroupManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.iam.IAMLoginProfileManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.iam.IAMPolicyManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.iam.IAMPolicyVersionManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.iam.IAMRoleManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.iam.IAMSSHPublicKeyManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.iam.IAMUserManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.iam.InstanceProfileManager
   :members:
   :show-inheritance:




Secondary Models
----------------

Secondary models are models that are used by the primary models to organize
their data. They are not acted on directly, but are used to describe the
structure of the fields in the primary models or other secondary models.



.. autopydantic_model:: botocraft.services.iam.AttachedPermissionsBoundary
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMRoleLastUsed
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMTag
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



.. autopydantic_model:: botocraft.services.iam.AccessKeyMetadata
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.AttachedPolicy
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.CreateAccessKeyResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.CreateGroupResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.CreateInstanceProfileResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.CreateLoginProfileResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.CreatePolicyResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.CreatePolicyVersionResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.CreateRoleResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.CreateServiceLinkedRoleResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.CreateUserResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.DeleteServiceLinkedRoleResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetAccessKeyLastUsedResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetGroupPolicyResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetGroupResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetInstanceProfileResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetLoginProfileResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetPolicyResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetPolicyVersionResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetRolePolicyResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetRoleResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetSSHPublicKeyResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetUserPolicyResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.GetUserResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.IAMAccessKeyLastUsed
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListAccessKeysResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListAttachedGroupPoliciesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListAttachedRolePoliciesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListAttachedUserPoliciesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListEntitiesForPolicyResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListGroupPoliciesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListGroupsForUserResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListGroupsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListInstanceProfilesForRoleResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListInstanceProfilesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListPoliciesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListPolicyVersionsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListRolePoliciesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListRolesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListSSHPublicKeysResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListUserPoliciesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.ListUsersResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.PolicyGroup
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.PolicyRole
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.PolicyUser
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.SSHPublicKeyMetadata
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.UpdateRoleDescriptionResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.iam.UploadSSHPublicKeyResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


