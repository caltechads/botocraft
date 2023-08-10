.. _runbook__contributing:

Contributing
============

Instructions for contributors
-----------------------------

Make a clone of the bitbucket repo:

.. code-block:: shell

    $ git clone git@bitbucket.org:caltech-imss-ads/caltech_docs.git


Workflow is pretty straightforward:

1. Make sure you are reading the latest version of this document.
2. Setup your machine with the required development environment
3. Make your changes.
4. Update the Sphinx documentation to reflect your changes.
5. ``cd doc; make clean && make html; open build/html/index.html``.  Ensure the docs
   build without crashing and then review the docs for accuracy.
6. ``terraform workspace select test; terraform init; terraform plan; terraform apply``
7. Commit changes to your branch.
8. Commit your changes into master.
9. Update your environemnt file and ``deploy config write test``
10. ``bumpversion <patch|minor|major>``.
11. ``make release``
12. Watch the ``#ads_deploys`` Slack channel to follow your deployment progress.


Preconditions for working on this project
-----------------------------------------

AWS credentials
^^^^^^^^^^^^^^^

The ``ADS-PROD`` account is part of the Caltech IMSS AWS Organization, and we use AWS
SSO to authenticate to this account.  Thus, to start with, you must have ``ADS-PROD``
listed among your available accounts when you do your SSO login.

Then, you MUST have a profile in your ``~/.aws/config`` which looks like this::

   [profile sso-ads-prod]
   sso_start_url = https://d-9267618a38.awsapps.com/start
   sso_region = us-west-2
   sso_account_id = 131067624433
   sso_role_name = AdministratorAccess
   region = us-west-2
   output = json


Docker
^^^^^^

Our current base image requires you to authenticate to AWS Public ECR in order to pull it.  Do:

.. code-block:: shell

    $ aws sso login
    $ aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
    $ docker pull public.ecr.aws/m3v9w5i2/caltech-imss-ads/amazonlinux2-python3.10


Python environment
^^^^^^^^^^^^^^^^^^

The Amazon Linux 2 base image we use here has Python 3.10.12, so we'll want that
in our virtualenv.

.. code-block:: shell

    $ pyenv virtualenv 3.10.12 caltech_docs
    $ pyenv local caltech_docs
    $ pip install --upgrade pip wheel
    $ pip install -r requirements.dev.txt

If you don't have a `pyenv` python 3.10.12 built, build it like so:

.. code-block:: shell

    $ pyenv install 3.10.12


terraform
^^^^^^^^^

You will need a recent version of ``terraform``, which can be installed with
homebrew.  Typically, we use the `chtf <https://github.com/Yleisradio/chtf>`_
terraform version switcher to manage our terraform versions.  At time of writing,
the recent terraform version was 1.5.4, but you can look at the `Terraform
Releases <https://github.com/hashicorp/terraform/releases>`_.  to see what the
current most recent version is.

.. code-block:: shell

   $ cd terraform-ads-prod-account
   $ brew install yleisradio/terraforms/chtf
   $ chtf 1.5.4
   $ cd terraform/app
   $ terraform workspace select test
   $ terraform init


Running the local docker stack
------------------------------

Install the environment file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Copy in the Docker environment file to the appropriate place on your Mac:

.. code-block:: shell

    $ cp etc/environment.txt /etc/context.d/caltech_docs.env

Build the Docker image
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    $ make build

Run the service and initialize the database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    $ make dev-detached
    $ make exec
    > ./manage.py migrate


Getting to the service in your browser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since {{ cookiecutter.project_name}} is meant to run behind the access.caltech
proxy servers, you'll need to supply the access.caltech HTTP Request headers in
order for it to work correctly. You'll need to use something like Firefox's
Modify Headers or Chrome's `ModHeader <https://bewisse.com/modheader/>`_ plugin
so that you can set the appropriate HTTP Headers.

Set the following Request headers:

* ``User`` to your access.caltech username
* ``SM_USER`` to your access.caltech username
* ``CAPCaltechUID`` to your Caltech UID,
* ``user_mail`` to your e-mail address
* ``user_first_name`` to your first name
* ``user_last_name`` to your last name

You should now be able to browse to `your app on localhost <https://localhost:8443/caltech_docs/docs/>`_ .

