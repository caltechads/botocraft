=========
botocraft
=========

.. toctree::
   :caption: Overview
   :hidden:

   overview/authoring

.. toctree::
   :caption: Runbook
   :hidden:

   runbook/contributing

.. toctree::
   :caption: Reference
   :hidden:

   api/models

Current version is |release|.

``botocraft`` is an opinionated re-implemenation of the AWS `boto3 <https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>`_ and `botocore <https://botocore.amazonaws.com/v1/documentation/api/latest/index.html>`_ python libraries.

Why make this library?
----------------------

While boto3 and botocore are wonderful libraries, and I honor the AWS teams for
making them available to us developers, one of the problems we have had is that
there is no standard interface in boto3 to all resources.  For example,
imagine you want to list a certain kind of resource:

* If you want to get a list of all ECS clusters, you use the ``list_clusters``
  method on the ``ecs`` client.  This returns a list of ARNs.  You then use
  ``describe_clusters`` to get the details of each of those ARNs.
  ``list_clusters`` can be paginated, but ``describe_clusters`` cannot, and can
  take a maximum of 10 ARNs.  So if you want to get the details of your clusters,
  you have to combine ``list_clusters`` and ``describe_clusters`` in chunks of 10.
* If you want to get a list of all EC2 instances, on the other hand, you use the
  ``describe_instances`` method on the ``ec2`` client.  This returns a list of detailed
  information about each instance.  ``describe_instances`` can be paginated.  There is
  no ``list_instances`` method.
* If you want to get a list of all S3 buckets, you use the ``list_buckets``
  method on the ``s3`` client.  This returns a list of bucket names.  There is no
  ``describe_buckets`` method.  And buckets are a mess of different resources,
  so to figure out how an S3 bucket is configured, you might have to make some or all
  of the following boto3 calls:
  * ``get_bucket_acl``
  * ``get_bucket_cors``
  * ``get_bucket_encryption``
  * ``get_bucket_lifecycle``
  * ``get_bucket_location``
  * etc.

This is just a small sampling of the inconsistencies in the boto3 API.  These
inconsistencies make it mandatory to have a deep understanding of the AWS API in
order to write code that interacts with consistently across codebases.

What does ``botocraft`` do?
---------------------------

It provides AWS resources as objects, with Django ORM-like managers that provide
a CRUDL and foreign key/many-to-many resolution like functionality for selected
AWS services.

.. note::
  You might ask, "Why not use the `AWS Cloud Control API
  <https://aws.amazon.com/cloudcontrolapi/>`_?".  While that does implement the
  CRUDL that we were looking for, we lose access to some of the more advanced
  features of the AWS API, like the ability to see the current status of a
  resource, or see ephemeral runtime or computed configuration.

  For example, ``describe_services`` in the ``ecs`` client returns the current
  deployments, events, task sets, running count, etc. for a service, but the
  ``get_resource`` for ``AWS::ECS::Service`` via the Cloud Control API does not.
  So we would have to make a call to the Cloud Control API to get a service, and
  then go back to ``boto3`` to use the ``ecs`` client to get the current status
  of the service.


Features
--------

* Provide AWS resources as Python classes, backed by `pydantic
  <https://github.com/pydantic/pydantic>`
* Automatically generate resource classes and manager classes by inspecting the
  ``botocore`` definitions, overlaid with our customizations
* Automatically paginate results if they are paginated in the AWS API
* Automatically resolve foreign keys and many-to-many relationships to resource objects