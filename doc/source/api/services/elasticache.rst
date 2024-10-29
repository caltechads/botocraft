

ElastiCache (elasticache)
=========================


Primary Models
--------------

Primary models are models that you can act on directly. They are the models that
represent resources in the AWS service, and are acted on by the managers.



.. autopydantic_model:: botocraft.services.elasticache.CacheCluster
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheParameterGroup
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheSecurityGroup
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheSubnetGroup
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ReplicationGroup
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json



Managers
--------

Managers work with the primary models to provide a high-level interface to the
AWS service. They are responsible for creating, updating, and deleting the
resources in the service, as well as any additional operations that are
available for those models.


.. autoclass:: botocraft.services.elasticache.CacheClusterManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.elasticache.CacheParameterGroupManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.elasticache.CacheParameterManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.elasticache.CacheSecurityGroupManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.elasticache.CacheSubnetGroupManager
   :members:
   :show-inheritance:

.. autoclass:: botocraft.services.elasticache.ReplicationGroupManager
   :members:
   :show-inheritance:




Secondary Models
----------------

Secondary models are models that are used by the primary models to organize
their data. They are not acted on directly, but are used to describe the
structure of the fields in the primary models or other secondary models.



.. autopydantic_model:: botocraft.services.elasticache.CacheNode
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheParameter
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheParameterGroupStatus
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheSecurityGroupMembership
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CloudWatchLogsDestinationDetails
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.EC2SecurityGroup
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ElastiCacheDestinationDetails
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ElastiCacheEndpoint
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ElastiCacheGlobalReplicationGroupInfo
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ElastiCacheNotificationConfiguration
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ElastiCachePendingModifiedValues
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ElastiCacheSlotMigration
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.KinesisFirehoseDestinationDetails
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.LogDeliveryConfiguration
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.NodeGroup
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.NodeGroupMember
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ParameterNameValue
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.PendingLogDeliveryConfiguration
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ReplicationGroupPendingModifiedValues
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ReshardingStatus
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.SecurityGroupMembership
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.UserGroupsUpdateStatus
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json



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



.. autopydantic_model:: botocraft.services.elasticache.AuthorizeCacheSecurityGroupIngressResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheClusterMessage
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheNodeTypeSpecificParameter
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheNodeTypeSpecificValue
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheParameterGroupDetails
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheParameterGroupNameMessage
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheParameterGroupsMessage
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheSecurityGroupMessage
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CacheSubnetGroupMessage
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CreateCacheClusterResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CreateCacheParameterGroupResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CreateCacheSecurityGroupResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CreateCacheSubnetGroupResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.CreateReplicationGroupResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.DeleteCacheClusterResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.DeleteReplicationGroupResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.LogDeliveryConfigurationRequest
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ModifyCacheClusterResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ModifyCacheSubnetGroupResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ModifyReplicationGroupResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.NodeGroupConfiguration
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.ReplicationGroupMessage
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.services.elasticache.RevokeCacheSecurityGroupIngressResult
    :show-inheritance:
    :inherited-members:
    :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


