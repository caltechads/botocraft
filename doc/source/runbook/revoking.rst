.. _runbook__revoking:

Revoking user privileges in caltech_docs
========================================

Problem
-------

Someone has access to the ``IMSS ADS Documentation`` application in
access.caltech, but you need to either remove some or all of their privileges
within the app, or you need to prevent them from accessing it at all.

Solution
--------

Remove permissions in the app
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See :doc:`/overview/authorization` for the levels of access available.

Currently, there's no UI for this, so we have to do it via the command line.  As
an example. we'll revoke Editor privileges from the user ``jdoe``.

.. code-block:: bash

    $ deploy exec prod
    $ ./manage.py shell_plus
    >>> user = User.objects.get(username='jdoe')
    >>> editors = Group.objects.get(name='Editors')
    >>> user.groups.remove(editors)
    >>> user.groups.values_list('name', flat=True)
    []

.. important::
    If you're removing privileges from a user, do the ``values_list()`` above to
    ensure that the user no longer has the privileges you're trying to remove.
    This means more than just checking that ``Editors`` is gone, above -- also
    ensure they don't have any additional privileges, such as ``Admins``,
    ``Project Managers`` etc.


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
    >>> Token.objects.filter(user=user).delete()

