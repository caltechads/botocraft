

Route 53 (route53)
==================


Primary Models
--------------

Primary models are models that you can act on directly. They are the models that
represent resources in the AWS service, and are acted on by the managers.



.. autopydantic_model:: botocraft.services.route53.CidrBlockSummary
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.HostedZone
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53CidrCollection
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53QueryLoggingConfig
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53ResourceRecordSet
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53VPC
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python



Managers
--------

Managers work with the primary models to provide a high-level interface to the
AWS service. They are responsible for creating, updating, and deleting the
resources in the service, as well as any additional operations that are
available for those models.


.. autoclass:: botocraft.services.route53.CidrBlockSummaryManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.route53.HostedZoneManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.route53.Route53CidrCollectionManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.route53.Route53QueryLoggingConfigManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.route53.Route53ResourceRecordSetManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.route53.Route53VPCManager
   :members:
   :show-inheritance:




Secondary Models
----------------

Secondary models are models that are used by the primary models to organize
their data. They are not acted on directly, but are used to describe the
structure of the fields in the primary models or other secondary models.



.. autopydantic_model:: botocraft.services.route53.HostedZoneConfig
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ResourceRecord
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53AliasTarget
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53CidrRoutingConfig
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53Coordinates
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53GeoLocation
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53GeoProximityLocation
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53LinkedService
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



.. autopydantic_model:: botocraft.services.route53.AssociateVPCWithHostedZoneResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Change
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ChangeBatch
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ChangeCidrCollectionResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ChangeInfo
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ChangeResourceRecordSetsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.CidrCollectionChange
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.CollectionSummary
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.CreateCidrCollectionResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.CreateHostedZoneResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.CreateQueryLoggingConfigResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.CreateVPCAssociationAuthorizationResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.DeleteCidrCollectionResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.DeleteHostedZoneResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.DeleteQueryLoggingConfigResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.DeleteVPCAssociationAuthorizationResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.DisassociateVPCFromHostedZoneResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.GetHostedZoneCountResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.GetHostedZoneLimitResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.GetHostedZoneResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.GetQueryLoggingConfigResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.HostedZoneLimit
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.HostedZoneOwner
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.HostedZoneSummary
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ListCidrBlocksResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ListCidrCollectionsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ListHostedZonesByNameResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ListHostedZonesByVPCResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ListHostedZonesResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ListQueryLoggingConfigsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ListResourceRecordSetsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.ListVPCAssociationAuthorizationsResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.Route53DelegationSet
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


.. autopydantic_model:: botocraft.services.route53.UpdateHostedZoneCommentResponse
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json, model_dump, construct, model_copy, model_validate, model_validate_json, model_validate_dict, model_validate_json_schema, model_validate_python, model_dump_json, model_dump_json_schema, model_dump_dict, parse_file, parse_obj, parse_raw, parse_json, parse_file_json, parse_file_dict, parse_file_json_schema, parse_file_python


