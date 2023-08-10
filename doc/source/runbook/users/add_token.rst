.. _runbook__users__add_token:

Adding an API token to a regular user
=====================================

Problem
-------

A normal human user wants to be able to use the ``caltech_docs`` API, but they don't
yet have an API token assigned to their user.

Solution
--------

We don't have a web interface for this yet, so you'll have to use the command line.

.. code-block:: bash

    $ deploy exec prod
    $ ./manage.py shell_plus
    >>> user = User.objects.get(username='jdoe')
    >>> Token.objects.create(user=user)
    <Token: e8490d42d7d125850321ba19702d8285b4214a98>

The value within the ``<Token: ...>``  is the token value.  The user can
then follow the instructions in :doc:`/overview/api` with that token value
to use the API.