.. _runbook__users__disabling:

Removing a user's access to "IMSS ADS Documentation"
====================================================

Problem
-------

Someone has access to the ``IMSS ADS Documentation`` application in
access.caltech, and you need to prevent them from accessing it at all.

Solution
--------

Remove caltech_docs role from user
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need to remove a user's access the access to the ``IMSS ADS
Documentation`` app entirely, this is done by removing the ``caltech_docs`` role
from the person in the ``Help Desk 2``.

#. Login to access.caltech.edu
#. Click on ``Help Desk 2``
#. Search for the user you want to grant ``IMSS ADS Documentation`` access to
#. Under ``Roles``, search for the ``caltech_docs`` role and uncheck the box
#. Click ``Save``

The user should now no longer see ``IMSS ADS Documentation`` in their list of
apps, under ``IMSS Internal``.


Revoke the user's API token, if present
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you've revoked the user's access from the ``IMSS ADS Documentation`` app in
access.caltech, also revoke their API token, if they have one.  Otherwise they
may still have at least read-only access to the data in the app through the API.

.. code-block:: bash

    $ deploy exec prod
    $ ./manage.py shell_plus
    >>> user = User.objects.get(username='username')
    >>> Token.objects.filter(user=user).delete()

