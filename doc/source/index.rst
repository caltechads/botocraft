============
caltech_docs
============

.. toctree::
   :caption: Overview
   :hidden:

   overview/authorization
   overview/api

.. toctree::
   :caption: Authoring Docs
   :hidden:

   overview/authoring
   overview/importing

.. toctree::
   :caption: Runbook
   :hidden:

   runbook/granting
   runbook/revoking
   runbook/users/enabling
   runbook/users/disabling
   runbook/users/add_token
   runbook/api_users/creating
   runbook/api_users/deleting
   runbook/api_users/get_token
   runbook/contributing

.. toctree::
   :caption: Reference
   :hidden:

   api/models
   api/rest
   api/terraform

Current version is |release|.

access.caltech name
    IMSS ADS Documentation

This Django access.caltech application provides private, authenticated access to
Sphinx documentation generated within IMSS ADS.   This uses the
`django-sphinx-hosting
<https://django-sphinx-hosting.readthedocs.io/en/latest/>`_ Django extension to
do most of the hard work.

This application was built so that we in ADS can use `Sphinx
<https://www.sphinx-doc.org/en/master/>`_  to author our code base documentation and have it
be published automatially to a system that is accessible only to Caltech
authenticated users.

This allows us to:

* have a single source of truth for our documentation
* have our documentation be private
* have our documentation be versioned with our code
* have our documentation be searchable

Features
--------

* Users must be authenticated via access.caltech, and authorized with the proper
  ``nsrole`` to view docs
* Users can be granted various levels of privileges within the system based on
  Django privileges
* Renders all documentation published within with a consistent theme
* You may multiple versions of your docs per project
* Navigation for each version of your documentation is automatially generated
  from the Sphinx table of contents
* Projects can be tagged with classifiers (like PyPI classifiers) to refine
  searching and filtering
* Projects can have external links associated with them
* Provides full-text search functionality across all projects
* Provides a REST API to programmatically interact with the system.  Useful for
  integrating into a CI/CD system.

AWS Architecture
----------------

.. thumbnail:: ../images/caltech_docs.png
   :alt: AWS architecture
   :title: AWS architecture