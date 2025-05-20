.. _runbook__contributing:

Contributing
============

Instructions for contributors
-----------------------------

Make a clone of the bitbucket repo:

.. code-block:: shell

    git clone https://github.com/caltechads/botocraft.git

Workflow is pretty straightforward:

1. Make sure you are reading the latest version of this document.
2. Setup your machine with the required development environment
3. Make your changes.
4. Update the Sphinx documentation to reflect your changes.
5. ``cd doc; make clean && make html; open build/html/index.html``. Ensure the
   docs build without crashing and then review the docs for accuracy.
6. Commit changes to your branch.
7. Merge your changes into master.
8. ``make release``.


Preconditions for working on this project
-----------------------------------------

AWS credentials
^^^^^^^^^^^^^^^

Set up your AWS credentials.  This is up to you and how your organization does it.


Python environment
^^^^^^^^^^^^^^^^^^

Install your Python environment with the following:

MacOS and Linux

    .. code-block:: shell

        curl -LsSf https://astral.sh/uv/install.sh | sh

    Now add the following to your ``~/.bash_profile`` or ``~/.zshrc``:

    .. code-block:: shell

        export PATH="$HOME/.local/bin:$PATH"

    Then run:


Regenerating the service classes
------------------------------

After you've made changes to the yaml files in ``botocraft/data``,  or to the
sync code in ``botocraft.sync`` you'll need to regenerate the service classes.
You can do this by running the following command:

    .. code-block:: shell

        botocraft sync


Testing out botocraft
----------------------

To test out your changes to botocraft, you can run the following command:

.. code-block:: shell

    botocraft shell


This will start an ipython shell with all botocraft service classes loaded. You can
then run commands like:

.. code-block:: python

    service = Service.objects.get('my-service', cluster='my-cluster')

.. important::

    The important part here is that the shell loads completely without any namespace or
    circular import errors.  If you see any errors, then you need to fix them before
    proceeding.

Updating the documentation
--------------------------

As you work on the app, put some effort into making the Sphinx docs build
cleanly and be accurate.

doc/source/index.rst
^^^^^^^^^^^^^^^^^^^^

* Check the "Overview" section and maybe update if you've added some big new
  features
* Check the "Important People" section and update as appropriate
* Check the "History" section and update as appropriate

autodoc
^^^^^^^

The api documentation is automatically generated from the docstrings in the generated
code, so there's nothing to do here for any code that gets generated into ``botocraft.services``.

For your own code (e.g. anything in ``botocraft.mixins``, ``botocraft.sync`` and
``botocraft.eventbridge``), please add appropriate documentation to your
classes, methods and attributes as docstrings, add them if appropriate to files
in ``doc/source/api/``.

etc.
^^^^

Review the other files to see if they need updating.

Then build the docs and look at them:

.. code-block:: shell

    cd doc
    make clean && make html
    open build/html/index.html

.. warning::

    This will take a looooong time, because the service docs are **huge**.

If you can build the docs with no critical errors and the docs seem to look ok
when you look through all the HTML pages, that's good enough at this point.


Releasing the code to PyPI
--------------------------

When you're ready to release the code to PyPI, if you're on a branch:

.. code-block:: shell

    git checkout master
    git pull
    git checkout <branch>
    git rebase master
    git checkout master
    git merge <branch>

This will pull anyone else's changes into your branch and then merge your branch into
master.

Then run the following command to bump the version number and create a new
distribution in PyPI:

.. code-block:: shell

    bumpversion <patch|minor|major>
    make release