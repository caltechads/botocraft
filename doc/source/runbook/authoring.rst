.. _overview_adding_resources:

How to add a new service to botocraft
=====================================

Problem
-------

``botocraft`` supports only a small subset of all possible AWS Services, and you
want to add support for an AWS service that ``botocraft`` does not yet support.

Solution
--------

Find the botocore service alias
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``botocraft`` has a command line tool that can help you find the botocore service
alias for the service you want to add.  Run the following command:

.. code-block:: bash

    botocraft botocore services

Look through the list of services and find the one you want to add.  From now on
we will refer to the service as ``<service_name>``.

Add the service to botocraft
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    botocraft botocore bootstrap <service_name>

This will create a new directory in ``botocraft/data/<service_name>`` with the
following files:

* A ``models.yml`` file to the ``botocraft/data/<service_name>`` directory.
  This will hold a list of primary and secondary models for the service.
* A ``manager.yml`` file to the ``botocraft/data/<service_name>`` directory.
  This will hold a list of manager definitions for the primary models of the service.

Find a primary model for the service and add a model definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For this we can use the ``botocraft botocore primary-models`` command to help
us.  This will parse the botocore definitions for the service and give us a list
all models in the file and their fields.   It can be a long list, because there
will be models for resources, for substructures used as types for resource
fields, request and response structures, exceptions, etc.

Here's an example of what the output looks like for the ``sns`` service:

.. code-block:: bash

    $ botocraft botocore primary-models sns
    PlatformApplication
        create_platform_application
        delete_platform_application
        get_platform_application_attributes
        list_endpoints_by_platform_application
        list_platform_applications
    Endpoint
        create_platform_endpoint
        delete_endpoint
        get_endpoint_attributes
    SMSSandboxPhoneNumber
        create_smssandbox_phone_number
        delete_smssandbox_phone_number
        list_smssandbox_phone_numbers
    Topic
        create_topic
        delete_topic
        get_topic_attributes
        list_topics
    Subscription: [READONLY]
        get_subscription_attributes
        list_subscriptions
        list_subscriptions_by_topic
    Tag: [READONLY]
        list_tags_for_resource

    ...

The non-indented bits are the model names.  The indented bits are the boto3
methods that (probably) act on the model.

.. note::

    This is really just a guess -- we look through all the model names, lowercase and snake-case them, then look for boto3 methods that
    have that string in them.  This is not a perfect heuristic, but it works
    as a starting point for finding the primary models for a service.
