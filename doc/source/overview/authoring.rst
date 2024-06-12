.. _overview_adding_resources:

How to add a service to botocraft
=================================

* Add a ``botocraft/data/<service_name>`` directory.  If this service was is
  named ``athena`` in the AWS SDK, then the directory would be
  ``botocraft/data/athena``.
* Add a ``models.yml`` file to the ``botocraft/data/<service_name>`` directory.
  This is a list of primary and secondary models for the service.
* Add a ``manager.yml`` file to the ``botocraft/data/<service_name>`` directory.
  This is a list of manager definitions for the primary models of the service.


