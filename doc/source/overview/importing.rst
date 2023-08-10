Importing your Sphinx docs into caltech_docs
============================================

Before importing your docs, ensure that you have configured your Sphinx project
properly for ``caltech_docs`` by following the instructions on
:doc:`/overview/authoring`.

In order to import your docs into ``caltech_docs``, you will need to:

#. Create a project in ``caltech_docs`` for your project.
#. Fulfill the prerequisites.
#. Build your docs as JSON files.
#. Package your docs as a tarfile.
#. Import that tarfile into ``caltech_docs``.

.. _overview_importing_create_project:

Creating a project in caltech_docs
----------------------------------

To create a project:

* Login to access.caltech
* Click "IMSS ADS Documentation"
* Click the "Create Project" button.  Fill out the form setting "Machine name"
  to what you set as ``project`` in your ``conf.py``, and click "Save".

Prerequisites
-------------

Follow the conventions
^^^^^^^^^^^^^^^^^^^^^^

Ensure that you have followed the conventions for your project type as outlined
in :doc:`/overview/authoring`.

Install dependencies
^^^^^^^^^^^^^^^^^^^^

Minimally, you'll need to install the Sphinx specific dependencies, including
any Sphinx extensions that you are using.  Typically, we list those in
``doc/requirements.txt``, so:

.. code-block:: shell

    $ pip install -r doc/requirements.txt

.. _overview_importing_autodoc:

autodoc
^^^^^^^

If you are using ``sphinx.ext.autodoc`` to automatically pull Python docstrings
into your Sphinx project, you will need to install your app and its dependencies
into the environment that you are using to build your docs.  This includes any

System dependencies
    ``autodoc`` imports your code in order to look at the ``__doc__`` attribute
    on your Python objects, and to do so, it needs all your Python dependencies
    installed.

    Some of your Python dependencies may be C or Rust, etc. extensions, and thus
    you may need to install system dependencies in order to build them: C
    headers, libraries, etc.  These typically require RPMs that need to be
    installed to get them on your system.  Examples: ``mysql-devel``,
    ``openldap-devel``.

Add this line to the top or bottom of your project ``requirements.txt`` file::

    -r doc/requirements.txt

No system dependencies
~~~~~~~~~~~~~~~~~~~~~~

If you have no system dependencies, then you can just do:

.. code-block:: shell

    $ pip install -r requirements.txt

Yes system dependencies
~~~~~~~~~~~~~~~~~~~~~~~

If you DO have system dependencies, it is mostly easier to build your docs
within your Docker container.  To do this, you'll need to ensure that
``doc/requirements.txt`` is added to your Docker image at the appropriate place.
For our typical Dockerfile, you want something like this:

.. code-block:: docker
    :emphasize-lines: 5

    # Install the latest pip and our dependencies into the virtualenv.  We do this
    # before copying the codebase so that minor code changes don't force a rebuild
    # of the entire virtualenv.
    COPY requirements.txt /tmp/requirements.txt
    COPY doc/requirements.txt /tmp/doc/requirements.txt
    RUN pip install --upgrade pip wheel && \
        pip install -r /tmp/requirements.txt && \
        rm -rf `pip cache dir`

Then you can safely build your docs with something like this baroque command line:

.. code-block:: shell

	$ docker run --rm \
        -v .:/docs \
        -w /app myapp \
        /bin/bash \
        -c "cd doc && rm -rf build && make json && cd build && tar zcf docs.tar.gz json && mv docs.tar.gz /docs"

.. important::
    For Django projects, you either will need to have defaults for all settings,
    or you will need to adjust the above command line to export add
    ``DJANGO_SETTINGS_MODULE=myapp.settings_docker`` at the ``make json`` step
    of the command.

    For other projects that have required settings, you'll need to deal with
    that on a a project-by-project basis.

    If you don't deal with this, your ``make json`` will fail because your app
    code won't finish bootstrapping.

Packaging
---------

Manual packaging
^^^^^^^^^^^^^^^^

In order to be able to be imported into ``caltech_docs``,  you will need to
publish your Sphinx docs as JSON files, and to bundle them in a specific way.

In your Sphinx docs folder, you will want to build your docs as ``json``, not
``html``.

Do either::

    make json

or::

    sphinx-build -n -b json build/json

To build the tarfile, the files in the tarfile should be contained in a folder.
We want::

    json/py-modindex.fjson
    json/globalcontext.json
    json/_static
    json/last_build
    json/genindex.fjson
    json/objectstore.fjson
    json/index.fjson
    json/environment.pickle
    json/searchindex.json
    json/objects.inv
    ...

Not::

    py-modindex.fjson
    globalcontext.json
    _static
    last_build
    genindex.fjson
    index.fjson
    environment.pickle
    searchindex.json
    objects.inv
    ...


Here's how you do that:

.. code-block:: shell

    $ cd build
    $ tar zcf docs.tar.gz json

Now you can import ``docs.tar.gz`` into ``caltech_docs``.

.. _overview_importing_makefile:

Makefile target
^^^^^^^^^^^^^^^

Add a ``Makefile`` target to your top-level project ``Makefile`` that will do
the needful for you.  For the below Makefile targets, when you copy them into
your Makefile, ensure that the indents are tabs, and not spaces.

.. note::
    If the below Makefile targets seem to be doing too much or to be a little
    overly complicated, it is because I've written these to work with our
    CodePipeline setup, specifically for the
    ``terraform-caltech-commons:codepipeline/actions/sphinx-docs`` CodeBuild
    step module.

    In the CodeBuild environment of course we don't have our requirements
    installed or our Docker image pulled, thus the extra steps.

No system dependencies
~~~~~~~~~~~~~~~~~~~~~~

You are a candidate for the below Makefile target if:

* You don't use ``autodoc`` at all in your Sphinx project (see
  :ref:`overview_importing_autodoc` for details).
* OR you do use ``autodoc`` but your python code has no C extensions, e.g.
  you don't use ``mysqlclient`` or ``python-ldap``
* OR This is not a python project.

.. code-block::

    docs:
        @echo "Installing docs dependencies ..."
        @pip install -r requirements.txt
        @echo "Generating docs..."
        @cd doc && rm -rf build && make json
        @cd doc/build && tar zcf docs.tar.gz json
        @mv doc/build/docs.tar.gz .
        @echo "New doc package is in docs.tar.gz"

Yes system dependencies
~~~~~~~~~~~~~~~~~~~~~~~

You are a candidate for the below Makefile target if:

* You ARE using ``autodoc`` in your Sphinx project (see
  :ref:`overview_importing_autodoc` for details).
* AND your project is a Django app.
* OR your project is not a Django app, but does need to use ``mysqlclient`` or
  uses ``python-ldap``.
* OR your project needs some other system dependency installed in order to build
  your docs.

.. code-block:: Makefile

    # Fix VERSION, PACKAGE and DOCKER_REGISTRY to be correct for your project
    VERSION = 0.1.0
    PACKAGE = my-project
    DOCKER_REGISTRY = 123456789012.dkr.ecr.us-west-2.amazonaws.com/org-name

    aws-login:
        # Login to ECR so we can pull our image
        @$(shell aws ecr get-login-password | docker login --password-stdin --username AWS ${REGISTRY}/${PACKAGE})

    pull:
        # Pull the image we want to build docs in
        docker pull ${DOCKER_REGISTRY}/${PACKAGE}:${VERSION}

    docs-dev:
        @echo "Installing docs dependencies ..."
        @pip install -r requirements.txt
        @echo "Generating docs..."
        @cd doc && rm -rf build && make json
        @cd doc/build && tar zcf docs.tar.gz json
        @mv doc/build/docs.tar.gz .
        @echo "New doc package is in docs.tar.gz"

    docs: aws-login pull
        # We build the docs in the container because it has all the dependencies
        # installed, most importantly including the system packages that are
        # required for the python packages to build.  This way we don't have to
        # manage those dependencies in the CodeBuild environment, which may be
        # different from the container environment.
        docker run --rm -v $(shell pwd):/docs -w /app ${DOCKER_REGISTRY}/${PACKAGE}:${VERSION} /bin/bash -c "cd doc && rm -rf build && make json && cd build && tar zcf docs.tar.gz json && mv docs.tar.gz /docs"


.. important::
    If you're going to use the above Makefile targets, and you want to build
    docs from your terraform code, ensure that your ``.dockerignore`` file does
    not exclude your terraform folders.  If it does, you'll see errors something
    like this::

        Sphinx-Terraform error:
        Definition not found for TerraformResourceSignature('TerraformBlockType.RESOURCE', 'aws_ecr_repository', 'repo') in module common.

    This is because the Sphinx pages reference your terraform files, but they're
    not in the container, so Sphinx can't find them.

Note there are two targets there: ``docs-dev`` and ``docs``.  ``docs-dev`` is
for when you are authoring your docs and want to build them locally (assuming
here you have a working virutalenv outside Docker).  ``docs`` is for when you
need to build your docs in a CodeBuild environment.

Importing
---------

There are three ways to import your package into ``caltech_docs``:

* Use the upload form on the project's detail page.
* Use the API endpoint ``/api/v1/version/``.
* Have your project CodePipeline automatially publish your docs to
  the API endpoint.

The upload form
^^^^^^^^^^^^^^^

To use the upload form, browse to the project detail page of the project whose
docs you want to import, and use the form titled "Import Docs" in the "Actions"
column along the left side of the page.

.. note::

    You must have the ``sphinxhostingcore.change_project`` Django permission or
    be a Django superuser in order to use the upload form.  Either assign that
    directly to your Django user object, or use assign your user to either the
    "Administrators" or "Editors" Django groups to get that permission.  See
    :doc:`/overview/authorization`


Use the API endpoint
^^^^^^^^^^^^^^^^^^^^

To upload your docs package via the API, you must submit as form-data, with a
single key named ``file``, and with the ``Content-Disposition`` header like
so::

    Content-Disposition: attachment;filename=mydocs.tar.gz

The filename you pass in the ``Content-Disposition`` header does not matter and
is not used; set it to whatever you want.

To upload a file with ``curl`` to the endpoint for this view:

.. code-block:: shell

    curl \
        -XPOST \
        -H "Authorization: Token __THE_API_TOKEN__" \
        -F 'file=@path/to/yourdocs.tar.gz' \
        https://caltech-docs-prod.api.ac.ads.caltech.internal/api/v1/version/import/

CodePipeline
^^^^^^^^^^^^

This is the preferred method of importing your docs into ``caltech_docs`` for us
ADS folk.

All of our standard CodePipeline modules from ``terraform-caltech-commons``
versions 0.36.0 and greater have a last step that will publish your docs to
the ``caltech_docs`` API.

To use this, you must:

* Have created a project in ``caltech_docs`` for your project.  See
  :ref:`overview_importing_create_project` for instructions.
* Have your Sphinx project in a folder called ``doc`` in the root of your
  project.
* Have a make target named ``docs`` that will build your docs tarfile, and
  will leave it named ``docs.tar.gz`` in the root of your project.  See :ref:`overview_importing_makefile` for instructions.

When you do your normal ``make release`` and push you changes to your ``build``
branch, the pipeline will kick off.  Since the publish docs step is the last
step in the pipeline, it will only run if all the other steps succeed.

Watch the Slack channel ``#ads_deploys`` for the results of your build.

.. note::
    If all you want to do is publish docs, and you have no source code to
    archive, Docker images to build or services or tasks to update, you can
    use the ``codepipeline/recipes/bitbucket-docs-only`` recipe from
    ``terraform-caltech-commons``.