

Cognito Identity Provider (cognito-idp)
=======================================


Primary Models
--------------

Primary models are models that you can act on directly. They are the models that
represent resources in the AWS service, and are acted on by the managers.



.. autopydantic_model:: botocraft.services.cognito_idp.CognitoGroup
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoIdentityProvider
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoResourceServer
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoUser
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoUserPool
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoUserPoolClient
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoUserPoolDomain
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python



Managers
--------

Managers work with the primary models to provide a high-level interface to the
AWS service. They are responsible for creating, updating, and deleting the
resources in the service, as well as any additional operations that are
available for those models.


.. autoclass:: botocraft.services.cognito_idp.CognitoGroupManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.cognito_idp.CognitoIdentityProviderManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.cognito_idp.CognitoResourceServerManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.cognito_idp.CognitoUserManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.cognito_idp.CognitoUserPoolClientManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.cognito_idp.CognitoUserPoolDomainManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.cognito_idp.CognitoUserPoolManager
   :members:
   :show-inheritance:




Secondary Models
----------------

Secondary models are models that are used by the primary models to organize
their data. They are not acted on directly, but are used to describe the
structure of the fields in the primary models or other secondary models.



.. autopydantic_model:: botocraft.services.cognito_idp.AccountRecoverySettingType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.AdminCreateUserConfigType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.AdvancedSecurityAdditionalFlowsType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.AnalyticsConfigurationType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.AttributeType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CustomDomainConfigType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CustomEmailLambdaVersionConfigType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CustomSMSLambdaVersionConfigType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.DeviceConfigurationType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.EmailConfigurationType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.EumsSmsConfigurationType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.FailoverType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.InboundFederationLambdaType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.IssuerConfigurationType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.KeyConfigurationType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.LambdaConfigType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.MFAOptionType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.MessageTemplateType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.NumberAttributeConstraintsType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.PasswordPolicyType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.PreTokenGenerationVersionConfigType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.RecoveryOptionType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.RefreshTokenRotationType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.ResourceServerScopeType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.RoutingType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.SchemaAttributeType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.SignInPolicyType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.SmsConfigurationType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.StringAttributeConstraintsType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.TokenValidityUnitsType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UserAttributeUpdateSettingsType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UserPoolAddOnsType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UserPoolPolicyType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UsernameConfigurationType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.VerificationMessageTemplateType
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



.. autopydantic_model:: botocraft.services.cognito_idp.AdminCreateUserResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.AdminDisableUserResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.AdminEnableUserResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.AdminGetUserResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.AdminResetUserPasswordResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.AdminSetUserPasswordResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoCreateGroupResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoGetGroupResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoListGroupsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CognitoListUsersResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CreateIdentityProviderResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CreateResourceServerResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CreateUserPoolClientResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.CreateUserPoolResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.DeleteUserPoolDomainResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.DescribeIdentityProviderResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.DescribeResourceServerResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.DescribeUserPoolClientResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.DescribeUserPoolDomainResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.DescribeUserPoolResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.ListIdentityProvidersResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.ListResourceServersResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.ListUserPoolClientsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.ListUserPoolsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.ProviderDescription
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UpdateGroupResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UpdateIdentityProviderResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UpdateResourceServerResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UpdateUserPoolClientResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UserPoolClientDescription
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.cognito_idp.UserPoolDescriptionType
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


