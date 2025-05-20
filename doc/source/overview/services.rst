botocraft AWS service models
============================

``botocraft`` provides a Django ORM-like interface to AWS resources.  This
interface is provided by models and managers.

When thinking of models in a botocraft context, think of them as
object-relational type objects for resources in an AWS service.  By resources,
we mean things in AWS that you manage via the AWS API.  For example,

* in ``ec2``, Instance, VPC, SecurityGroup, etc are resources
* in ``autoscaling``, AutoScalingGroup, LaunchConfiguration, etc are resources
* in ``ecs``, Cluster, TaskDefinition, Service, etc are resources
* etc.

There are three types of models in botocraft:

Primary models
  These are models that you can perform AWS API operations on directly.

Secondary models
  These are models that are used to build out the sub-structure of primary
  models.  Some fields on primary models are of secondary model types.

Request/Response models
  These are models that are used to represent the request and response
  structures of AWS API operations.  You will typically not use directly by
  the user, but are used by the botocraft code generator to generate the
  primary and secondary models.

Importing models
----------------

All models are available via the ``botocraft.services`` module.  You can import them
without having to know the service they are in.  For example, to import the
``Service`` model from ``ecs``:

.. code-block:: python

    from botocraft.services import Service

    service = Service.objects.get('my-service')

Available services
------------------

.. include:: _services_list.rst

Primary models
--------------

A primary model is a model that you can perform boto3 operations on directly.  They
map to a single AWS resource type.  Primary models have managers that implement
operations that can be performed on a primary model.  The manager is available
as the ``.objects`` attribute of a primary model class object, vaguely similar to
how Django ORM works.

For example, in ``ecs`` one primary model is ``Service``.  You can create, read,
update, and delete a ``Service``, like so:

.. code-block:: python

    from botocraft.services import Service

    # create a service
    service = Service(
        serviceName='my-service',
        clusterArn='arn:aws:ecs:us-west-2:123456789012:cluster/my-cluster',
        roleArn='arn:aws:iam::123456789012:role/my-ecs-service-role',
        taskDefinition='my-task-def:3',
        desiredCount=1
    )
    service.objects.create(service)

    # or
    # service.save()

    # Update the service
    service.desiredCount = 2
    service.save()

    # Get a different service
    service = Service.objects.get(service='my-service-2', cluster='other-cluster')

    # Delete the service
    service.delete()

Sessions
^^^^^^^^

You may need to manage multiple AWS accounts and regions in the same codebase.
``botocraft`` provides a way to do this via sessions, which are simply
``boto3.session.Session`` objects bound to the proper account user or role.

To use a specific session, you can use the ``using`` method on the manager.  For
example:

.. code-block:: python

    from botocraft.models import Service

    session = boto3.session.Session(
        aws_access_key_id='my-access-key',
        aws_secret_access_key='my-secret-key',
        region_name='us-west-2'
    )

    service = Service.objects.using(session).get('my-service', cluster='my-cluster')

Managers
--------

A manager is an object that implements operations that can be performed on a
primary model.  These map python methods to boto3 operations.

The manager will have methods for at least some of the CRUDL operations:
``create``, ``get``, ``update``, ``partial_update``, ``delete``, and ``list``,
and occasionally a ``get_many`` (which is somewhere between a ``get`` (for a
single object) and a ``list`` (all objects).   Some primary models are read only
primary models will not have ``create``, ``update``, and ``delete`` methods, or
are create-only (can't be updated), and will not have an ``update`` method.
The interface all depends on the AWS service and the resource type.

* ``create`` - create a new resource.  You define a primary model object and
  pass it into ``Model.objects.create(obj)``.  It usually returns the object
  as retrieved from AWS after the creation completes, but check the documentation.
* ``get`` - get a single resource.  You use the primary key for the model (which is
  resource dependent, typically one of ``name``, ``id``, ``arn``) and pass it
  pass it into with the appropriate args and keyword arguments.  For example,
  ``Model.objects.get('my-resource')``.
* ``update`` - update a resource.  ``get`` the object from its primary key, make
  changes to the object, and then call ``save`` on the object.  This calls ``update``
  on the manager.
* ``partial_update`` - instead of using ``update`` some models offer a ``partial_update``
  method.  This allows you to pass in the primary key for the model, plus any other
  keyword arguments that you want to update.  For example,
  ``Model.objects.partial_update('my-resource', attribute=2)``.
* ``delete`` - delete a resource by passing in the primary key for the model.
* ``get_many`` - get many resources.  This is somewhere between a ``get`` (for a
  single object) and a ``list`` (all objects).  The signature of this varies by
  resource type.  And the number of items available to be returned will vary
  also. This will not exist for all models.
* ``list`` - list all resources of a given type.  For example, ``Model.objects.list()``.
  ``list`` will handle any pagination required by the AWS API, and often will offer
  ways to filter or refine your resulting list of objects.  This will depend on the
  resource.

The manager may also have other methods for performing resource specific
operations that are not CRUDL operations.  For example, ``SecurityGroup`` from the
``ec2`` service has a ``authorize_ingress`` method that allows you to add ingress
rules to a security group.  Look at the documentation for the resource type to
see what other methods are available.  These are added purposefully to the
manager by the botocraft developers.

Simple properties
^^^^^^^^^^^^^^^^^

Most models implement some simple properties to get typical attributes of the
model like ``name``, ``pk`` and ``arn``.  These are shorthands so that we don't
need to inspect the model object to get the particular, resource-specific
attribute.

All models will have a ``pk`` property that returns the primary key for the
model, but not all models will have ``name`` or ``arn`` properties.

For ``pk``, the primary key is always a dict, and it should be in the form needed
to be passed into the manager's ``get`` method.

.. code-block::

  >>> from botocraft.models import Service
  >>> service = Service.objects.get('my-service')
  >>> print(service.pk)
  {'service': 'my-service', 'cluster': 'my-cluster'}
  >>> print(service.arn)
  'arn:aws:ecs:us-west-2:123456789012:service/my-cluster/my-service'

There may be more such simple properties available on a model, depending on the
resource type and model definition.

Relationships
^^^^^^^^^^^^^

Some primary models have relationships with other primary models.  These are
python properties, not methods.  For example, in ``ecs``,
:py:class:`botocraft.services.ecs.Service` has a relationship with
:py:class:`botocraft.services.ecs.TaskDefinition`.
:py:meth:`botocraft.services.ecs.Service.task_definition`` is a property that
returns a :py:class:`botocraft.services.ecs.TaskDefinition`` object that is
associated with the service via its
:py:class:`botocraft.service.ecs.Service.taskDefinition` attribute, which is the
ARN of the task definition.

.. code-block:: python

  from botocraft.models import Service

  # Get a service
  service = Service.objects.get('my-service')

  # Get the task definition for the service
  task_definition = service.task_definition

Some relationships are implemented as ``@cached_property`` properties if we know they
won't change during our use of the model object.  Others are implemented as
``@property`` properties if we know they might change during our use of the model.

Relationships are not available for all primary models.

Manager method proxies
^^^^^^^^^^^^^^^^^^^^^^

Some primary models have proxies to manager methods on them, typically so you
can use a non-CRUDL method that takes a single resource directly from the
primary model instance.

For example, in ``ecr``, the :py:class:`botocraft.models.ecr.Image` model has a
:py:meth:`botocraft.models.ecr.Image.scan_findings` method that is a proxy to
the :py:meth:`botocraft.managers.ecr.ImageManager.scan_findings` method,
returning only the findings for that image.

Manager method proxies are not available for all primary models.

Secondary models
----------------

A secondary model is a model that is used as sub structure of a primary model.
For instance, in ``ecs``, ``Service`` is a primary model and
``LoadBalancerConfiguration`` is a secondary model that you assign to
``Service.loadBalancers``, in order to configure load balancers for the service.

Example:

.. code-block:: python

    from botocraft.services import Service, LoadBalancerConfiguration

    # Create a service with a load balancer
    service = Service(
        serviceName='my-service',
        clusterArn='arn:aws:ecs:us-west-2:123456789012:cluster/my-cluster',
        roleArn='arn:aws:iam::123456789012:role/my-ecs-service-role',
        taskDefinition='my-task-def:3',
        desiredCount=1,
        loadBalancers=[
            LoadBalancerConfiguration(
                targetGroupArn='arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/my-targets/2453ed029918f21f',
                containerName='my-app',
                containerPort=80
            )
        ]
    )
    service.objects.create(service)

Some primary models are quite complicated and have many secondary models, or
they may have none.

Secondary models themselves can have other secondary models as types for their
attributes.  For example, ``Container``, a secondary model of ``TaskDefinition``
itself, uses ``NetworkBinding``, ``NetworkInterface`` and ``ManagedAgent``
secondary models.