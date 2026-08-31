Managing Cognito users manually
================================

``botocraft`` exposes the Amazon Cognito user pool (``cognito-idp``) admin API
through :py:class:`~botocraft.services.cognito_idp.CognitoUser` and
:py:class:`~botocraft.services.cognito_idp.CognitoUserManager`. Use these when
you need to create, look up, or update users out-of-band -- for example from a
migration script, an admin CLI, or a backend job -- rather than having users
self-register through hosted UI or an SDK-driven sign-up flow.

This page covers user management specifically. For everything else on a user
pool (the pool itself, app clients, groups, identity providers, resource
servers), see :doc:`/api/services/cognito_idp`.

.. note::

   Cognito *identity pools* (``cognito-identity``,
   :py:class:`~botocraft.services.cognito_identity.CognitoIdentityPool`) are a
   separate service and do not have a "user" concept. An identity pool only
   tracks anonymous or federated *identities* -- bare IDs with no profile,
   created implicitly the first time a caller exchanges login tokens for
   AWS credentials. There is no create/update API for an identity; see
   :py:class:`~botocraft.services.cognito_identity.CognitoIdentity` for the
   readonly lookup surface. If you need actual user accounts -- usernames,
   passwords, attributes, group membership -- that is always ``cognito-idp``.

Imports
-------

.. code-block:: python

    from botocraft.services.cognito_idp import (
        AttributeType,
        CognitoGroup,
        CognitoUser,
    )

Every ``CognitoUser`` operation is scoped to a user pool, so you always pass
``UserPoolId`` explicitly -- there is no "current pool" context.

Create a user
--------------

Use :py:meth:`~botocraft.services.cognito_idp.CognitoUserManager.create`,
which wraps ``admin_create_user``. This is the out-of-band equivalent of a
user signing themselves up:

.. code-block:: python

    user = CognitoUser.objects.create(
        CognitoUser(
            Username="ada@example.com",
            UserPoolId="us-east-1_AbCdEfGhI",
            UserAttributes=[
                AttributeType(Name="email", Value="ada@example.com"),
                AttributeType(Name="email_verified", Value="true"),
                AttributeType(Name="given_name", Value="Ada"),
            ],
        ),
        UserPoolId="us-east-1_AbCdEfGhI",
        DesiredDeliveryMediums=["EMAIL"],
    )
    print(user.Username, user.UserStatus)

By default AWS emails the user a temporary password and marks them
``FORCE_CHANGE_PASSWORD``. Pass ``MessageAction="SUPPRESS"`` if you're setting
a password out-of-band yourself and don't want Cognito to send an invite:

.. code-block:: python

    user = CognitoUser.objects.create(
        CognitoUser(
            Username="grace@example.com",
            UserPoolId="us-east-1_AbCdEfGhI",
            UserAttributes=[
                AttributeType(Name="email", Value="grace@example.com"),
            ],
        ),
        UserPoolId="us-east-1_AbCdEfGhI",
        MessageAction="SUPPRESS",
    )

Look up a user
---------------

Use :py:meth:`~botocraft.services.cognito_idp.CognitoUserManager.get`. It
returns ``None`` if the username doesn't exist in that pool:

.. code-block:: python

    user = CognitoUser.objects.get(
        UserPoolId="us-east-1_AbCdEfGhI",
        Username="ada@example.com",
    )
    if user is None:
        raise RuntimeError("user not found")

    print(user.UserStatus, user.Enabled)
    for attr in user.UserAttributes or []:
        print(attr.Name, attr.Value)

List users in a pool
---------------------

Use :py:meth:`~botocraft.services.cognito_idp.CognitoUserManager.list`, scoped
by ``UserPoolId``. You can also pass a Cognito search ``Filter`` (e.g.
``'email = "ada@example.com"'``) to narrow the results server-side:

.. code-block:: python

    users = CognitoUser.objects.list(UserPoolId="us-east-1_AbCdEfGhI")
    for user in users:
        print(user.Username, user.UserStatus)

    verified_only = CognitoUser.objects.list(
        UserPoolId="us-east-1_AbCdEfGhI",
        Filter='email_verified = "true"',
    )

Update a user's attributes
----------------------------

Cognito has no single "replace the whole user" update operation -- only
:py:meth:`~botocraft.services.cognito_idp.CognitoUserManager.partial_update`,
which wraps ``admin_update_user_attributes`` and patches just the attributes
you pass:

.. code-block:: python

    CognitoUser.objects.partial_update(
        UserPoolId="us-east-1_AbCdEfGhI",
        Username="ada@example.com",
        UserAttributes=[
            AttributeType(Name="given_name", Value="Augusta Ada"),
            AttributeType(Name="custom:plan", Value="pro"),
        ],
    )

To clear an attribute, submit it with a blank value:

.. code-block:: python

    CognitoUser.objects.partial_update(
        UserPoolId="us-east-1_AbCdEfGhI",
        Username="ada@example.com",
        UserAttributes=[AttributeType(Name="custom:plan", Value="")],
    )

``partial_update`` returns ``None`` -- re-``get()`` the user afterward if you
need the refreshed attribute list.

Enable or disable sign-in
---------------------------

Use :py:meth:`~botocraft.services.cognito_idp.CognitoUserManager.disable` and
:py:meth:`~botocraft.services.cognito_idp.CognitoUserManager.enable` to block
or restore a user's ability to authenticate, without deleting their account:

.. code-block:: python

    CognitoUser.objects.disable(
        UserPoolId="us-east-1_AbCdEfGhI",
        Username="ada@example.com",
    )

    # ... later ...

    CognitoUser.objects.enable(
        UserPoolId="us-east-1_AbCdEfGhI",
        Username="ada@example.com",
    )

Delete a user
--------------

.. code-block:: python

    CognitoUser.objects.delete(
        UserPoolId="us-east-1_AbCdEfGhI",
        Username="ada@example.com",
    )

This permanently removes the account. There is no soft-delete; use
``disable()`` above if you just want to suspend access.

Manage group membership
-------------------------

Groups (:py:class:`~botocraft.services.cognito_idp.CognitoGroup`) are how
Cognito models coarse-grained authorization (e.g. ``admins``, ``billing``).
Create the group once, then attach/detach users with the ``Admin*`` group
operations:

.. code-block:: python

    group = CognitoGroup.objects.create(
        CognitoGroup(
            GroupName="admins",
            UserPoolId="us-east-1_AbCdEfGhI",
            Description="Full admin access",
        ),
        UserPoolId="us-east-1_AbCdEfGhI",
    )

.. note::

   ``botocraft`` currently generates full CRUDL for
   :py:class:`~botocraft.services.cognito_idp.CognitoGroup` itself, but the
   add/remove-user-from-group and list-groups-for-user operations
   (``admin_add_user_to_group``, ``admin_remove_user_from_group``,
   ``admin_list_groups_for_user``) are not yet wrapped as manager methods.
   Until they are, call them directly against the boto3 client:

   .. code-block:: python

       CognitoGroup.objects.client.admin_add_user_to_group(
           UserPoolId="us-east-1_AbCdEfGhI",
           Username="ada@example.com",
           GroupName="admins",
       )

Common pitfalls
-----------------

* Every ``CognitoUser`` and ``CognitoGroup`` manager method requires
  ``UserPoolId`` explicitly -- there is no ambient "current pool."
* ``create()`` sends AWS's default invitation email/SMS unless you pass
  ``MessageAction="SUPPRESS"``.
* ``partial_update()`` only patches the attributes you list; it does not
  accept a full user model and returns ``None``, not the updated user.
* ``disable()``/``enable()`` control sign-in only -- they do not touch group
  membership, attributes, or the underlying account.
* ``delete()`` is permanent. Prefer ``disable()`` for reversible suspension.
* Don't confuse this page with ``cognito-identity`` -- identity pools have no
  user accounts, only ephemeral federated/anonymous identities. See the note
  at the top of this page.

See also
---------

* :doc:`/overview/services` for general model/manager/session usage
* :doc:`/api/services/cognito_idp` for the complete generated ``cognito-idp``
  API reference (pools, app clients, groups, identity providers, resource
  servers, domains)
* :doc:`/api/services/cognito_identity` for the ``cognito-identity``
  (identity pool) API reference
