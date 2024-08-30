.. _overview_adding_resources:

How to add a new service to botocraft
=====================================

Find the botocore service alias
-------------------------------

Find the official alias of the service in botocore github repository.  Look here
for the list of services: `botocore/services
<https://github.com/boto/botocore/tree/develop/botocore/data>`_.  The alias is
the name of the directory in the ``botocore/data`` directory.

.. important::

    The github listing in that folder will look like this:

    .. thumbnail:: /_static/images/botocore_services.png
       :width: 100%
       :alt: botocore services

    Now that we see stuff like ``accessanalyzer/2019-11-01``.  The alias is the
    bit before the slash.  So in this case, the alias is ``accessanalyzer``.

    If there are more dated definitions for the service, then you won't see
    the date in the alias.  For example, ``cloudfront``.  In that case, just
    use the name of the directory.

From now on we will refer to the service as ``<service_name>``.

Add the service to botocraft
----------------------------

* Add a ``botocraft/data/<service_name>`` directory.  If this service was is
  named ``elasticache`` in the AWS SDK, then the directory would be
  ``botocraft/data/elasticache``.
* Add a ``models.yml`` file to the ``botocraft/data/<service_name>`` directory.
  This is a list of primary and secondary models for the service.
* Add a ``manager.yml`` file to the ``botocraft/data/<service_name>`` directory.
  This is a list of manager definitions for the primary models of the service.

Find a primary model for the service and add a model definition
---------------------------------------------------------------

For this we can use the ``botocraft inspect models`` command to help us.  This
will parse the botocore definitions for the service and give us a list all
models in the file and their fields.   It can be a long list, because there will
be models for resources, for substructures used as types for resource fields,
request and response structures, exceptions, etc.


.. code-block:: bash

    $ botocraft inspect models <service_name>
    APICallRateForCustomerExceededFault:
    AddTagsToResourceMessage:
        ResourceName: string -> String
        Tags: list -> TagList
    AllowedNodeTypeModificationsMessage:
        ScaleUpModifications: list -> NodeTypeList
        ScaleDownModifications: list -> NodeTypeList
    Authentication:
        Type: string -> AuthenticationType
        PasswordCount: integer -> IntegerOptional
    AuthenticationMode:
        Type: string -> InputAuthenticationType
        Passwords: list -> PasswordListInput
    AuthorizationAlreadyExistsFault:
    AuthorizationNotFoundFault:
    AuthorizeCacheSecurityGroupIngressMessage:
        CacheSecurityGroupName: string -> String
        EC2SecurityGroupName: string -> String
        EC2SecurityGroupOwnerId: string -> String
    AuthorizeCacheSecurityGroupIngressResult:
        CacheSecurityGroup: structure -> CacheSecurityGroup
    AvailabilityZone:
        Name: string -> String
    BatchApplyUpdateActionMessage:
        ReplicationGroupIds: list -> ReplicationGroupIdList
        CacheClusterIds: list -> CacheClusterIdList
        ServiceUpdateName: string -> String
    BatchStopUpdateActionMessage:
        ReplicationGroupIds: list -> ReplicationGroupIdList
        CacheClusterIds: list -> CacheClusterIdList
        ServiceUpdateName: string -> String
    CacheCluster:
        CacheClusterId: string -> String
        ConfigurationEndpoint: structure -> Endpoint
        ClientDownloadLandingPage: string -> String
        CacheNodeType: string -> String
        Engine: string -> String
        EngineVersion: string -> String
        CacheClusterStatus: string -> String
        NumCacheNodes: integer -> IntegerOptional
        PreferredAvailabilityZone: string -> String
        PreferredOutpostArn: string -> String
        CacheClusterCreateTime: timestamp -> TStamp
        PreferredMaintenanceWindow: string -> String
        PendingModifiedValues: structure -> PendingModifiedValues
        NotificationConfiguration: structure -> NotificationConfiguration
        CacheSecurityGroups: list -> CacheSecurityGroupMembershipList
        CacheParameterGroup: structure -> CacheParameterGroupStatus
        CacheSubnetGroupName: string -> String
        CacheNodes: list -> CacheNodeList
        AutoMinorVersionUpgrade: boolean -> Boolean
        SecurityGroups: list -> SecurityGroupMembershipList
        ReplicationGroupId: string -> String
        SnapshotRetentionLimit: integer -> IntegerOptional
        SnapshotWindow: string -> String
        AuthTokenEnabled: boolean -> BooleanOptional
        AuthTokenLastModifiedDate: timestamp -> TStamp
        TransitEncryptionEnabled: boolean -> BooleanOptional
        AtRestEncryptionEnabled: boolean -> BooleanOptional
        ARN: string -> String
        ReplicationGroupLogDeliveryEnabled: boolean -> Boolean
        LogDeliveryConfigurations: list -> LogDeliveryConfigurationList
        NetworkType: string -> NetworkType
        IpDiscovery: string -> IpDiscovery
        TransitEncryptionMode: string -> TransitEncryptionMode

    ...

The non-indented bits are the model names.  The indented bits are the fields of
the model.

.. note::

  Note that the field types here are botocore ``Shape`` names, which are either simple
  types like ``Boolean``, ``String``, ``Integer``, etc., or they are references to other
  models in the file (e.g. ``CacheParameterGroupStatus``)

We look through the list and find a model that represents a primary resource
for the service.  For this you'll have to use your judgement by looking at the
``boto3`` documentation for the service and seeing what kind of operations exist
and what they act on.

.. hint::

  Let's say we are looking at the ``elasticache`` service.  We look at the ``boto3``
  docs and see operations like

  * ``create_cache_cluster``
  * ``delete_cache_cluster``
  * ``describe_cache_clusters``
  * ``modify_cache_cluster``
  * ``reboot_cache_cluster``

  So there's a good chance that the ``CacheCluster`` model is a primary model for
  the service.

Generally, looking for a ``describe_*`` operation is a good place to start -- it means
there's at least a readonly resource that you can get details about, and that makes it
a primary model.
