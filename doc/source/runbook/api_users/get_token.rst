.. _runbook__users__get_token:

Getting the API token for a user
================================

Problem
-------

A user (API or human) has an API token assigned, but we don't know what it is.

Solution
--------

API Users
^^^^^^^^^

For API users, you can use the ``list_api_users`` command to get a list of
users with their tokens:

.. code-block:: bash

    $ deploy exec prod
    $ ./manage.py list_api_users
    Username    Full name    Contact email               Auth Token                                Created
    ----------  -----------  --------------------------  ----------------------------------------  ----------
    api-test                 imss-ads-staff@caltech.edu  a35044f5309d02335dab2ebdfa1fcc8ce6d1ebda  2023-05-10
    api-test2                cmalek+test2@caltech.edu    593597e7763ded3f9c909a8ba97150d46d501196  2023-07-31

Human users
^^^^^^^^^^^

For human users:

.. code-block:: bash

    $ deploy exec prod
    $ ./manage.py shell_plus
    >>> user = User.objects.get(username='jdoe')
    >>> user.auth_token.key
    e8490d42d7d125850321ba19702d8285b4214a98