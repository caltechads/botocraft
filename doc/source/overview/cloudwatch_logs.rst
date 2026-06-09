CloudWatch Logs search and query
================================

``botocraft`` exposes CloudWatch Logs through
:py:class:`~botocraft.services.logs.LogGroup` and
:py:class:`~botocraft.services.logs.QueryDefinition`, with Insights polling
helpers in :py:mod:`botocraft.mixins.logs`.

This page focuses on searching log events with CloudWatch Logs Insights and
managing saved query definitions. For the full generated API, see
:doc:`/api/services/logs`. For CloudWatch metrics and metric streams, see
:doc:`/overview/cloudwatch`.

.. note::

   The ``logs`` service is not the ``cloudwatch`` service. Log groups, log
   streams, and Insights queries live under ``logs``
   (:doc:`/api/services/logs`).

Imports
-------

Overview examples import from the logs service module:

.. code-block:: python

    import time
    from datetime import UTC, datetime, timedelta

    from botocraft.services.logs import LogGroup, QueryDefinition

If your application uses a non-default session, call
``LogGroup.objects.using(session)`` and ``QueryDefinition.objects.using(session)``
the same way as other services (see :doc:`/overview/services`).

LogGroup
--------

A :py:class:`~botocraft.services.logs.LogGroup` represents one CloudWatch log
group. Resolve it by name, then call Insights operations on the instance —
:py:meth:`~botocraft.services.logs.LogGroup.start_query`,
:py:meth:`~botocraft.services.logs.LogGroup.get_query_results`, and
:py:meth:`~botocraft.services.logs.LogGroup.get_fields` bind ``logGroupName``
from the model so you do not repeat it on every call.

Find a log group
~~~~~~~~~~~~~~~~

.. code-block:: python

    log_group = LogGroup.objects.get(logGroupName="/aws/lambda/my-function")

    if log_group is None:
        raise RuntimeError("log group not found")

Inspect available fields
~~~~~~~~~~~~~~~~~~~~~~~~

Before writing a query, discover which fields appear in recent log events:

.. code-block:: python

    for field in log_group.get_fields():
        print(field.name, f"{field.percent:.1f}%")

Pass ``time`` (epoch seconds) to center the field scan on a specific window;
otherwise AWS searches the most recent 15 minutes.

Search logs with Insights
-------------------------

CloudWatch Logs Insights queries are asynchronous: ``start_query`` returns a
``queryId``, then you poll ``get_query_results`` until the status is terminal.

``startTime`` and ``endTime`` are Unix epoch **seconds**. Convert datetimes
explicitly before calling AWS:

.. code-block:: python

    end = int(datetime.now(tz=UTC).timestamp())
    start = int((datetime.now(tz=UTC) - timedelta(hours=1)).timestamp())

Botocraft exposes several layers depending on how much orchestration you want:

.. list-table::
   :header-rows: 1
   :widths: 24 36 40

   * - Layer
     - Method
     - Use when
   * - Start (instance)
     - :py:meth:`~botocraft.services.logs.LogGroup.start_query`
     - You have a ``LogGroup`` and manage polling yourself
   * - Poll (instance)
     - :py:meth:`~botocraft.services.logs.LogGroup.get_query_results`
     - You want one status/result page or manual ``nextToken`` control
   * - Start (manager)
     - :py:meth:`~botocraft.services.logs.LogGroupManager.start_query`
     - You query multiple groups or do not have a model instance
   * - Wait (manager mixin)
     - :py:meth:`~botocraft.mixins.logs.LogGroupManagerMixin.wait_for_query_results`
     - You want to block until a terminal query status
   * - One-shot (manager mixin)
     - :py:meth:`~botocraft.mixins.logs.LogGroupManagerMixin.run_query`
     - You want start, wait, and aggregated result pages in one call

Start a query on a log group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:py:meth:`~botocraft.services.logs.LogGroup.start_query` takes ``startTime``,
``endTime``, and ``queryString`` as positional arguments. Optional keyword
arguments include ``queryLanguage`` (``CWLI``, ``SQL``, or ``PPL``) and
``limit``:

.. code-block:: python

    start_response = log_group.start_query(
        start,
        end,
        (
            "fields @timestamp, @message "
            "| filter @message like /ERROR/ "
            "| sort @timestamp desc "
            "| limit 20"
        ),
        limit=20,
    )
    query_id = start_response.queryId

Poll and read results
~~~~~~~~~~~~~~~~~~~~~

Call :py:meth:`~botocraft.services.logs.LogGroup.get_query_results` on the
same ``LogGroup`` instance. The log group name is not part of this call —
results are keyed by ``queryId`` only:

.. code-block:: python

    while True:
        page = log_group.get_query_results(query_id)
        if page.status != "Running":
            break
        time.sleep(1.0)

    print(page.status)
    for row in page.results or []:
        print({field.field: field.value for field in row})

Each row is a list of :py:class:`~botocraft.services.logs.ResultField` objects
with ``field`` and ``value`` attributes. Inspect ``page.statistics`` for
``recordsMatched``, ``recordsScanned``, and ``bytesScanned``.

Paginate large result sets
~~~~~~~~~~~~~~~~~~~~~~~~~~

When a query returns more rows than one page holds, follow ``nextToken``:

.. code-block:: python

    all_rows = []
    next_token = None

    while True:
        page = log_group.get_query_results(
            query_id,
            nextToken=next_token,
            maxItems=10_000,
        )
        all_rows.extend(page.results or [])
        next_token = page.nextToken
        if next_token is None:
            break

End-to-end search example
~~~~~~~~~~~~~~~~~~~~~~~~~

Put discovery, start, poll, and print together:

.. code-block:: python

    log_group = LogGroup.objects.get(logGroupName="/ecs/my-service")
    end = int(datetime.now(tz=UTC).timestamp())
    start = int((datetime.now(tz=UTC) - timedelta(hours=1)).timestamp())

    # Optional: see which fields are common before writing the query
    for field in log_group.get_fields(time=end):
        print(field.name, f"{field.percent:.1f}%")

    start_response = log_group.start_query(
        start,
        end,
        "fields @timestamp, @message | filter @message like /ERROR/ | limit 50",
    )
    query_id = start_response.queryId

    while True:
        page = log_group.get_query_results(query_id)
        if page.status != "Running":
            break
        time.sleep(1.0)

    if page.status != "Complete":
        raise RuntimeError(f"query finished with status {page.status}")

    for row in page.results or []:
        values = {field.field: field.value for field in row}
        print(values["@timestamp"], values["@message"])

Manager alternatives
~~~~~~~~~~~~~~~~~~~~

Use the manager when you need capabilities the instance methods do not cover.

**Multiple log groups** — pass ``logGroupNames`` or ``logGroupIdentifiers`` to
the manager instead of binding a single group:

.. code-block:: python

    start_response = LogGroup.objects.start_query(
        startTime=start,
        endTime=end,
        queryString="fields @message | stats count()",
        logGroupNames=["/ecs/service-a", "/ecs/service-b"],
    )

**Block until complete** — after ``log_group.start_query``, delegate waiting to
the manager mixin (``queryId`` is not log-group-specific):

.. code-block:: python

    start_response = log_group.start_query(start, end, "fields @message | limit 100")
    final = LogGroup.objects.wait_for_query_results(
        start_response.queryId,
        poll_interval=1.0,
        max_attempts=120,
    )

**One-shot automation** — ``run_query`` starts, waits, and collects all result
pages. It requires ``logGroupNames`` on the manager call:

.. code-block:: python

    rows, stats = LogGroup.objects.run_query(
        queryString="stats count() by bin(5m)",
        logGroupNames=["/ecs/my-service"],
        startTime=start,
        endTime=end,
    )

    print(stats.recordsMatched, stats.bytesScanned)
    for row in rows:
        print({field.field: field.value for field in row})

``run_query`` raises :py:exc:`RuntimeError` when the query finishes in a
non-complete terminal status.

Pitfalls
~~~~~~~~

* ``startTime``/``endTime`` must be epoch seconds, not ``datetime`` objects
* ``Running`` on the first poll is normal; an empty first page is not a failure
* Large result sets require ``nextToken`` pagination; paginate manually or use
  ``run_query``
* Cross-account queries usually need ``logGroupIdentifiers`` with ARNs on the
  manager ``start_query`` call
* Query cost scales with scanned bytes; inspect ``statistics.bytesScanned``

Saved query definitions
-----------------------

Use :py:class:`~botocraft.services.logs.QueryDefinition` to store reusable
Insights queries in CloudWatch Logs.

Create and list definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    definition = QueryDefinition(
        name="error-count-by-service",
        queryString="fields @message | filter @message like /ERROR/ | stats count()",
        logGroupNames=["/ecs/my-service"],
    )
    definition = QueryDefinition.objects.create(definition)

    saved = QueryDefinition.objects.get(definition.queryDefinitionId)
    all_defs = QueryDefinition.objects.list(queryDefinitionNamePrefix="error-")

``QueryDefinition.objects.list()`` returns all pages. Botocore does not ship a
paginator for ``describe_query_definitions``, so Botocraft adds a list
decorator that loops ``nextToken`` transparently.

Run a saved definition
~~~~~~~~~~~~~~~~~~~~~~

:py:meth:`~botocraft.services.logs.QueryDefinitionManager.start_query` uses the
saved ``queryString`` and ``logGroupNames`` from the definition:

.. code-block:: python

    start_response = saved.start_query(
        startTime=start,
        endTime=end,
    )
    query_id = start_response.queryId

When the definition targets a single log group you already have as a model,
poll results through that instance:

.. code-block:: python

    log_group = LogGroup.objects.get(logGroupName=saved.logGroupNames[0])

    while True:
        page = log_group.get_query_results(query_id)
        if page.status != "Running":
            break
        time.sleep(1.0)

Or use ``LogGroup.objects.wait_for_query_results(query_id)`` when you only need
the final response without manual polling.
