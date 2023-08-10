.. _overview_authoring:

How to write your Sphinx docs
=============================

``caltech_docs`` expects your Sphinx documentation project to be structured,
configured, and authored in a particular way for maximum compatibility once it
is imported into the system.

Read these documents from ``django-sphinx-hosting`` closely and follow
the instructions therein:

* :doc:`django-sphinx-hosting:overview/authoring`
* :doc:`django-sphinx-hosting:overview/packaging`

.. note::
    The ``ads-prod`` branches of both ``ads-django-cookiecutter`` and
    ``ads-script-cookiecutter`` project templates provide properly configured
    starting Sphinx projects that start out compatible with ``caltech_docs``,
    so if you are adding docs to an old project, you might look at those
    templates to see what you need to do.

caltech_docs conventions
------------------------

In addition to the instructions in the above documents, ``caltech_docs`` and the
CodePipeline auto-publishing system have a few additional conventions:

The "doc" folder
^^^^^^^^^^^^^^^^

Your Sphinx project should live in ``doc``.

Your project repository should be minimally structured as follows::

    ├── doc
    │   ├── Makefile
    │   ├── requirements.txt
    │   └── source
    │       ├── _images
    │       ├── _static
    │       ├── conf.py
    │       └── index.rst
    ├── requirements.txt
    ├── .bumpversion.cfg
    └── my_project
       ├── __init__.py
       └── ...

doc/requirements.txt
^^^^^^^^^^^^^^^^^^^^

The minimal contents for ``doc/requirements.txt`` should be::

    Sphinx                                        # https://github.com/sphinx-doc/sphinx
    sphinx_rtd_theme
    sphinxcontrib-jsonglobaltoc                   # https://github.com/caltechads/sphinxcontrib-jsonglobaltoc
    sphinxcontrib-images
    # We use our own version of sphinx-terraform that fixes a bug in the
    # the upstream version that has yet to be merged
    git+https://gitlab.com/cmalek1/sphinx-terraform.git

conf.py
^^^^^^^

Set the ``project`` variable in your Sphinx ``conf.py`` to the name of your git
repository.

The ``release`` variable in your sphinx ``conf.py`` should match the version of
the code you're deploying -- this is the version that will be used for the
project version in the IMSS ADS Documentation application.

Example:

.. code-block:: python

   import os
   import sys
   from typing import List, Dict, Tuple, Optional
   import sphinx_rtd_theme  # pylint: disable=unused-import  # noqa:F401
   # -- Path setup --------------------------------------------------------------
   sys.path.insert(0, os.path.abspath('../..'))

   # -- Project information -----------------------------------------------------

   # This should match the project machine name in the IMSS ADS Documentation
   # application
   project: str = 'my_project'
   # This should match the version of the code you're deploying
   release: str = '0.1.0'