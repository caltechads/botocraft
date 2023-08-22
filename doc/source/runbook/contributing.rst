.. _runbook__contributing:

Contributing
============

Instructions for contributors
-----------------------------

Make a clone of the git repo:

.. code-block:: shell

    $ git clone git@github.com/caltechads/botocraft.git


Workflow is pretty straightforward:

1. Make sure you are reading the latest version of this document.
2. Setup your machine with the required development environment
3. Make your changes.
4. Update the Sphinx documentation to reflect your changes.
5. ``cd doc; make clean && make html; open build/html/index.html``.  Ensure the docs
   build without crashing and then review the docs for accuracy.
7. Commit changes to your branch.
8. Commit your changes into master.
9. ``bumpversion patch`` or ``bumpversion minor`` to bump the version number.
10. ``git push --tags origin master`` to push the new version tag to the repo.
11. ``make release`` to release the new version to PyPI.


Preconditions for working on this project
-----------------------------------------


Python environment
^^^^^^^^^^^^^^^^^^

The Amazon Linux 2 base image we use here has Python 3.10.12, so we'll want that
in our virtualenv.

.. code-block:: shell

    $ pyenv virtualenv 3.10.12 botocraft
    $ pyenv local botocraft
    $ pip install --upgrade pip wheel
    $ pip install -r requirements.txt

If you don't have a `pyenv` python 3.10.12 built, build it like so:

.. code-block:: shell

    $ pyenv install 3.10.12


TBD