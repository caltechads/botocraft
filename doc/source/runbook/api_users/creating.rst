.. _runbook__api_user__create:

Creating an API user in caltech_docs
====================================

Problem
-------

In order to access the ``caltech_docs`` API at
https://caltech-docs-prod.api.ac.ads.caltech.internal/api/v1/ programmatically
(i.e. from another script or service), you must have an API user.

.. note::
    This document covers creating an API-only user for the ``caltech_docs`` app.
    You would use this if you want to access the API programmatically as a user
    other than an actual access.caltech human user.

    Human users can have their own API keys, so if you're looking to access the
    API as a human user, see :doc:`/runbook/users/add_token`.

Solution
--------

There is currently no way to create an API user through the web interface. You
must use the command line instead.

Create the user
^^^^^^^^^^^^^^^

We use the ``manage_api_user`` Django management command to create or update
an API user.   This command is available on the ``caltech_docs`` server.

To create an API user, run the following command on the ``caltech_docs`` server:

.. code-block:: bash

    $ deploy exec prod
    $ ./manage.py manage_api_user <username> \
        --email <email> \
        --first-name <first_name> \
        --last-name <last_name>
    Created APIUser object for  (api-<username>): ID=3
    Token for api-test2: 593597e7763ded3f9c909a8ba97150d46d501196

.. note::
    We'll automatically prepend ``api-`` to any username you provide.  This is
    so that we can see at a glance that this is an API user.

For ``<email>`` set this to the email address of the person who will be using
the API user.  This is used to send notifications about the API user.

For ``<first_name>`` and ``<last_name>`` set these so that they describe the
purpose of the user.  For example, if this is for a script that will be
run from a CodePipeline set to upload documentation to ``caltech_docs``, you
could set ``<first_name>`` to "CodePipeline" and ``<last_name>`` to the "Uploader".

We really just want to set the ``<first_name>`` and ``<last_name>`` to something
that allows us to identify the use case when we list the API users.

(optional) Assign the user to permission groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

API Users with no groups assigned have read-only access to the API.  API users
must be assigned to permission groups in order to be able to create, modify, or
delete objects via the API.  See :doc:`/overview/authorization` for more
information about the available permission groups.

Here is an example of adding an API user named ``api-test`` to the ``Version
Managers`` group, allowing them to create, modify, and delete
:py:class:`sphinx_hosting.models.Version` objects via the API.

.. code-block:: bash

    $ deploy exec prod
    $ ./manage.py shell_plus
    >>> user = User.objects.get(username='api-test')
    >>> group = Group.objects.get(name='Version Managers')
    >>> user.groups.add(group)
    >>> user.groups.values_list('name', flat=True)
    ['Version Managers']


