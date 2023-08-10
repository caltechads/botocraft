.. _overview_authorization:

User authorization
==================

access.caltech
--------------

``caltech_docs`` is an access.caltech app, listed on the access.caltech home
page as "IMSS ADS Documentation". As such, authentication is handled by the
access.caltech environment.  Users must have a valid access.caltech account to
log in to the appropriate environment, and then browse to the application from
the access.caltech application list.

To reach the application within the access.caltech environment users must have
the ``cn=caltech_docs,ou=people,ou=imss,o=caltech,c=us`` role in the ``nsrole``
attribute of their CAP LDAP record.

To assign or revoke access at the access.caltech level, see:

* :doc:`/runbook/users/enabling`
* :doc:`/runbook/users/disabling`

Django permissions
------------------

Once a user has authenticated to access.caltech and has been granted access to
to the application at the access.caltech level, Django determines what they can
do within the system based on their Django permissions.

API users (see :ref:`overview_api`) are subject to the same Django permissions
as human users.

The following Django groups to exist in the system, each assigning users to
different levels of privileges.

.. important::
    Users who are assigned to none of these groups are ``Viewers``: they can
    search and read the documentation sets within, but they cannot create,
    modify or delete anything.

Administrators
^^^^^^^^^^^^^^

Users in the ``Administrators`` group have full privileges within the system.

* Create, edit, delete :py:class:`sphinx_hosting.models.Project` objects
* Create, edit, delete :py:class:`sphinx_hosting.models.Version` objects
* Create, edit, delete :py:class:`sphinx_hosting.models.Classifier` objects

Editors
^^^^^^^

Users in the ``Editors`` group can work with projects and versions but have no
rights to manage :py:class:`sphinx_hosting.models.Classifier` objects.

* Create, edit, delete :py:class:`sphinx_hosting.models.Project` objects
* Create, edit, delete :py:class:`sphinx_hosting.models.Version` objects


Project Managers
^^^^^^^^^^^^^^^^

Users in the ``Project Managers`` group can create, edit and delete
:py:class:`sphinx_hosting.models.Project` objects.


Version Managers
^^^^^^^^^^^^^^^^

Users in the ``Version Managers`` group can create, edit and delete
:py:class:`sphinx_hosting.models.Version` objects.

Classifier Managers
^^^^^^^^^^^^^^^^^^^

Users in the ``Classifier Managers`` group can create, edit and delete
:py:class:`sphinx_hosting.models.Classifier` objects.

Managing permissions
--------------------

The following pages describe how to manage user permissions within the system.

* :doc:`/runbook/granting`
* :doc:`/runbook/revoking`
