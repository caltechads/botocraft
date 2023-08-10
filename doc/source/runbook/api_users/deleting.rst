.. _runbook__api_user__deleting:

Deleting an API user in caltech_docs
====================================

Problem
-------

We no longer need an existing API user and we want to delete it.

Solution
--------

There is currently no way to delete an API user through the web interface. You
must use the command line instead.

Delete the user
^^^^^^^^^^^^^^^

.. code-block:: bash

    $ deploy exec prod
    $ ./manage.py shell_plus
    >>> APIUser.objects(name='api-test').delete()
