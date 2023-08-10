.. _runbook__granting:

Granting user privileges in caltech_docs
========================================

Problem
-------

You want to modify permissions for a user within in  ``IMSS ADS Docmumentation``
application in access.caltech.edu.  This page also applies to granting permissions
to an API user (see :doc:`/overview/api`).

Solution
--------

See :doc:`/overview/authorization` for the levels of access available.

The user must exist in order for us to assign privileges to them.

* For human users, this means they have to have accessed ``IMSS ADS
  Documentation`` at least once before you can grant them permissions, otherwise
  their user won't exist in Django.
* For API users, this means the user has been created via the procedure at
  :doc:`/runbook/api_users/creating`.

Currently, there's no UI for this, so we have to do it via the command line.  As
an example. we'll grant the user ``jdoe`` Editor privileges.

.. code-block:: bash

    $ deploy exec prod
    $ ./manage.py shell_plus
    >>> user = User.objects.get(username='jdoe')
    >>> editors = Group.objects.get(name='Editors')
    >>> user.groups.add(editors)
    >>> user.groups.values_list('name', flat=True)
    ['Editors']
    >>> exit

.. note::

    If you're granting permissions to an API user, usernames are all prefixed
    by ``api-``.  You can list all API users with:

    .. code-block:: bash

        $ deploy exec prod
        $ ./manage.py list_api_users
        Username    Full name    Contact email               Auth Token                                Created
        ----------  -----------  --------------------------  ----------------------------------------  ----------
        api-test                 imss-ads-staff@caltech.edu  a35044f5309d02335dab2ebdfa1fcc8ce6d1ebda  2023-05-10
        api-test2                cmalek+test2@caltech.edu    593597e7763ded3f9c909a8ba97150d46d501196  2023-07-31