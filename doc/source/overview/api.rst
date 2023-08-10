.. _overview_api:

The caltech_docs REST API
=========================

``caltech_docs`` provides a REST API for interacting with the the application in
a programmatic way. The API is implemented using `Django REST Framework
<https://www.django-rest-framework.org/>`_.

How to reach the API
--------------------

The API is reachable at the following URL:
https://caltech-docs-prod.api.ac.ads.caltech.internal/api/v1/

This is a private URL that is only reachable from within AWS VPCs.

This API endpoint is reachable from the application subnets of the following
VPCs:

* ``ACS-PROD:ads-utils``
* ``ACS-PROD:ads-production``
* ``ACS-PROD:acs-infrastructure``
* ``ADS-PROD:utils``
* ``ADS-PROD:web``

If you are not in one of these VPCs, to access the API you will need to use an
SSH tunnel to a host in one of these VPCs.

Authentication
--------------

The ``caltech_docs`` API uses Token based authentication.   To use the API you
must either have an :py:class:`caltech_docs.users.models.APIUser` in the system,
or a human Django user with a :py:class:`rest_framework.authtoken.models.Token`
attached to it.

API Users are for use by code that is not associated with a human user.  For
example, the ADS CodePiplines use an API user to access the API to upload new
documentation sets after a successful deploy of an application to test.

.. note::
    See :doc:`/runbook/api_users/creating` for more information on creating
    API users.

    See :doc:`/runbook/users/add_token` for more information on adding a Token
    to a human user.

    See :doc:`/runbook/api_users/get_token` for information on how to get the
    actual auth token for a user.


Then, on each access to the API, the caller must supply an ``Authorization`` request
header on each of your requests that looks like so::

    Authorization: Token b422b0e7d1d11f5060613c01c4ccd1b00174b876

replacing that hex string with your actual authoriztion token.  Note that the
auth token should be preceeded with the string literal "``Token``" with
whitespace separating the two strings.

Here's a properly formatted ``curl`` line that will hit the ``/api/v1/projects/``
endpoint:

.. code-block:: bash

    $ curl -X GET \
          -H "Accept: application/json; indent=4" \
          -H "Authorization: Token b422b0e7d1d11f5060613c01c4ccd1b00174b876" \
          --insecure \
          --verbose \
          https://caltech-docs-prod.api.ac.ads.caltech.internal/api/v1/projects/

.. note::
    The ``--insecure`` flag is required because the API is only available via
    HTTPS, and the certificate is self-signed.

Pagination of list results
--------------------------

All list results are paginated, with the default page size of 100 items.   We
paginate because a some of the queries are very costly,  especially if you're
getting a list result of a model with lots of rows.

Your results will all look something like this:

.. code-block::

    GET /api/v1/projects/

.. code-block:: json

    {
        "count": 123,
        "next": "https://caltech-docs-prod.api.ac.ads.caltech.internal/api/v1/projects/?limit=100&offset=100",
        "previous": null,
        "results": [
            [ ... ]
        ]
    }

* To get to the next page of your results, ``GET`` the URL from the ``next`` key
  from the result dict
* To get the previous page, ``GET`` the URL from the ``prev`` key from the result dict.

To get a different number of results per page, use the ``limit`` param:

.. code-block::

    GET /api/v1/projects/?limit=50

will retrieve 50 projects instead of 100.