.. _querysets:

Querysets
=========

Understanding QuerySets
-----------------------

When you call ``.list()`` methods in Botocraft, they don't return simple lists
of objects. Instead, they return a :py:class:`PrimaryBoto3ModelQuerySet` object - a
powerful wrapper around your AWS resources that provides a Django-like interface
for filtering, ordering, and manipulating collections of objects.

Unlike Django, QuerySets in ``botocraft`` are NOT lazy - they fetch all data
from AWS before any applying any QuerySet method.  This is because there is no
commonality across all the AWS services on how to list results; some require
parameters, some don't, and some have pagination and some don't, etc.  So you
start with a ``.list()`` method to get a QuerySet, and then you can use
QuerySet methods to filter, order, and manipulate that data.

Basic Usage
-----------

When you call a ``.list()`` method on any manager, you get a queryset:

.. code-block:: python
    >>> from botocraft import Instance, Bucket
    >>> from botocraft import PrimaryBoto3ModelQuerySet

    # Get all EC2 instances
    >>> instances = Instance.objects.list()
    >>> isinstance(instances, PrimaryBoto3ModelQuerySet)
    True

    # Get all S3 buckets
    >>> buckets = Bucket.objects.list()
    >>> isinstance(buckets, PrimaryBoto3ModelQuerySet)
    True

    # QuerySets can be iterated over
    >>> for instance in instances:
    ...     print(instance.name)
    i-1234567890abcdef0
    i-0987654321fedcba0
    i-1122334455667788
    ...

    # QuerySets can be converted to lists
    >>> instance_list = list(instances)
    >>> isinstance(instance_list, list)
    True

Working with QuerySets
----------------------

You must call ``.list()`` to get a QuerySet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before you can use any QuerySet methods, you must call the ``.list()`` method
on the manager. The reason is that there is no commonality across all AWS API calls on how to list results.

All ``.list()`` methods return a
:py:class:`PrimaryBoto3ModelQuerySet`, which behaves like a Django QuerySet but is
not lazy. This means it fetches all data from AWS immediately when you call
``.list()`` and then allows you to filter, order, and manipulate that data.

.. code-block:: python

    >>> from botocraft import Instance

    >>> instances = Instance.objects.list()  # Fetches all instances
    >>> isinstance(instances, PrimaryBoto3ModelQuerySet)
    True

To illustrate how different objects have different ``.list()`` implementations, consider ECS Service vs ECS Cluster.

To list ECS services, you would use:

.. code-block:: python

    >>> from botocraft import Service

    >>> services = Service.objects.list(cluster="my_cluster")  # Fetches all ECS services in the specified cluster

Here, ``cluster`` is required to specify which ECS cluster to list services
from, otherwise you always get the ``default`` cluster.

On the other hand, to list ECS Clusters, you would use:

.. code-block:: python

    >>> from botocraft import Cluster

    >>> clusters = Cluster.objects.list()  # Fetches all ECS clusters

Note that this doesn't require any parameters, as it lists all clusters in your account.

Thus, we need to first call ``.list()`` to get a QuerySet, passing in any
required parameters, which then allows us to use QuerySet methods like
``filter()``, ``order_by()``, and others.

Filtering
---------

The most common operation is filtering results using :py:meth:`PrimaryBoto3ModelQuerySet.filter`:

.. code-block:: python

    >>> from botocraft import Instance

    # Get all running instances
    >>> running_instances = Instance.objects.list().filter(state__name="running")

    # Get all t2.micro instances
    >>> micro_instances = Instance.objects.list().filter(instance_type="t2.micro")

    # Combining filters (AND logic)
    >>> instances = Instance.objects.list().filter(
    ...     state__name="running",
    ...     instance_type="t2.micro"
    ... )

    # Chaining filters
    >>> instances = (
    ...     Instance.objects
    ...     .list()
    ...     .filter(state__name="running")
    ...     .filter(instance_type="t2.micro")
    ... )

Chained filters are ANDed together, so the above is equivalent to:

.. code-block:: python
    >>> from botocraft import Instance

    >>> instances = (
    ...     Instance.objects
    ...     .list()
    ...     .filter(
    ...         state__name="running",
    ...         instance_type="t2.micro"
    ...     )
    ... )

Advanced Filtering
~~~~~~~~~~~~~~~~~~

``botocraft`` provides Django-like lookup expressions for filtering:

.. code-block:: python

    >>> from botocraft import Instance

    # Case-insensitive contains, in this case against a dict, and comparing
    # against the value of the dict
    >>> instances = Instance.objects.list().filter(tags__icontains="prod")

    # Exact match for keys in a dict
    >>> instances = Instance.objects.list().filter(tags__has_key="Environment")

    # Greater than
    >>> instances = Instance.objects.list().filter(volume_size__gt=100)

    # In a list of values
    >>> instances = Instance.objects.list().filter(instance_type__in=["t2.micro", "t3.micro"])

    # Regular expressions
    >>> instances = Instance.objects.list().filter(name__regex=r"web-\d+")

    # Case-insensitive regex
    >>> instances = Instance.objects.list().filter(name__iregex=r"WEB-\d+")

    # Filtering datetime fields
    >>> instances = Instance.objects.list().filter(launch_time__year=2023)
    >>> instances = Instance.objects.list().filter(launch_time__month=6)
    >>> instances = Instance.objects.list().filter(launch_time__date="2023-06-01")

These are only some of the available lookups. You can use any field lookup supported by
:py:class:`PrimaryBoto3ModelQuerySet.filter`, which includes:

- ``exact``, ``iexact``
- ``contains``, ``icontains``
- ``startswith``, ``istartswith``
- ``endswith``, ``iendswith``
- ``regex``, ``iregex``
- ``in``
- ``gt``, ``gte``, ``lt``, ``lte``
- ``isnull``
- For datetime fields: ``date``, ``year``, ``month``, ``day``, ``hour``, ``minute``, ``second``, ``week``, ``week_day``, ``quarter``

Filtering on dictionaries
-------------------------

You can filter on dictionary fields (like tags) using the double underscore syntax:
.. code-block:: python

    >>> from botocraft import Instance

    # Filter instances with a specific tag key, regardless of value
    >>> instances = Instance.objects.list().filter(tags__has_key="Environment")

    # Filter instances with a specific tag value
    >>> instances = Instance.objects.list().filter(tags__Environment="Production")

    # Filter instances with a tag key and value
    >>> instances = Instance.objects.list().filter(tags__has_key="Owner", tags__Environment="Production")

    # Filter instances where a tag contains a substring
    >>> instances = Instance.objects.list().filter(tags__Environment__icontains="prod")

Ordering
--------

Sort your results with ``.order_by()``:

.. code-block:: python

    from botocraft import Instance

    # Order by
    >>> instances = Instance.objects.list().order_by("tags__Name")

    # Descending order (prefix with -)
    instances = Instance.objects.list().order_by("-launch_time")

    # Order by nested attributes
    instances = Instance.objects.list().order_by("tags__Name")

Retrieving a Single Object
--------------------------

Get the first object matching your filters:

.. code-block:: python

    from botocraft import Instance

    # Get the first running instance
    >>> instance = Instance.objects.list().filter(state__name="running").first()

    # Returns None if no objects match
    >>> instance = Instance.objects.list().filter(name="nonexistent").first()
    >>> instance is None
    True

Accessing Items
---------------

Access items using indexing or slicing:

.. code-block:: python

    from botocraft import Instance
    # Get all instances
    >>> instances = Instance.objects.list()

    # Get the first instance
    >>> first_instance = instances[0]

    # Get a slice
    >>> first_three = instances[0:3]
    >>> len(first_three)
    3

    # Get every other instance
    >>> every_other = instances[::2]

Checking Results
----------------

Check if your query actually matched some models:

.. code-block:: python

    from botocraft import Instance

    # Get all running instances
    >>> instances = Instance.objects.list().filter(state__name="running")
    >>> if instances.exists():
    ...    print("Found instances!")

    # Or use boolean evaluation
    >>> if instances:
    ...    print("Found instances!")

Counting Results
~~~~~~~~~~~~~~~~

Count the number of results:

.. code-block:: python

    from botocraft import Instance

    # Get all running instances and count them
    >>> instances = Instance.objects.list().filter(state__name="running")
    >>> instances.count()  # Returns the number of running instances
    35

    # Alternatively, you can use the len() function
    >>> len(instances)
    35

Iteration over results
----------------------

Iterate through results just like a regular list:

.. code-block:: python

    from botocraft import Instance

    >>> instances = Instance.objects.list()
    >>> for instance in instances:
    ...    print(instance.name)
    i-1234567890abcdef0
    i-0987654321fedcba0
    i-1122334455667788
    ...

Getting a list of value dictionaries
------------------------------------

If you just need a list of specific field values, you can use ``.values()``:

.. code-block:: python

    from botocraft import Instance

    # Get a list of instance names
    >>> instance_names = Instance.objects.list().values("instanceId")
    [{"instanceId": "i-1234567890abcdef0"}, {"instanceId": "i-0987654321fedcba0"}, ...]

    # Get a list of instance IDs and types
    >>> instance_info = Instance.objects.list().values("instanceId", "instance_type")
    [{"id": "i-1234567890abcdef0", "instance_type": "t2.micro"}, {"id": "i-0987654321fedcba0", "instance_type": "t3.micro"}, ...]

Getting a python list of a single field
---------------------------------------

If you need a simple list of a single field's values, you can use ``.values_list()``:

.. code-block:: python

    from botocraft import Instance

    # Get a list of instance IDs as a list of tuples
    >>> instance_ids = Instance.objects.list().values_list("instanceId")
    [("i-1234567890abcdef0",), ("i-0987654321fedcba0",), ...]

    # Get a list of instance names as a flat list
    >>> instance_names = Instance.objects.list().values_list("name", flat=True)
    ["web-server-1", "db-server-1", ...]

Chaining Operations
-------------------

You can chain multiple operations together:

.. code-block:: python

    from botocraft import Instance

    # Filter, order, and slice in one line
    >>> result = Instance.objects.list().filter(state__name="running").order_by("name")[0:5]
    >>> result.count()
    5

    # Complex example
    >>> instances = (
    ...     Instance.objects.list()
    ...     .filter(tags__Key="Environment", tags__Value="Production")
    ...     .filter(instance_type__in=["t2.micro", "t3.micro"])
    ...     .order_by("-launch_time")
    ... )