CloudWatch metrics and metric streams
=====================================

``botocraft`` exposes the CloudWatch control plane through
:py:class:`~botocraft.services.cloudwatch.CloudWatchMetric` and
:py:class:`~botocraft.services.cloudwatch.CloudWatchMetricStream`, with
managers and model-bound helpers in
:py:mod:`botocraft.mixins.cloudwatch`.

This page focuses on discovering metric time series, publishing and reading
datapoints, and operating metric streams. For alarms, dashboards, insight rules,
and other primaries, see :doc:`/api/services/cloudwatch`.

.. note::

   The ``cloudwatch`` service is not CloudWatch Logs. Log groups and log streams
   live under the separate ``logs`` service
   (:doc:`/api/services/logs`).

Imports
-------

Overview examples import from the CloudWatch service module:

.. code-block:: python

    from datetime import UTC, datetime, timedelta

    from botocraft.services.cloudwatch import (
        CloudWatchDimension,
        CloudWatchMetric,
        CloudWatchMetricStream,
        CloudWatchMetricStreamStatisticsConfiguration,
    )

If your application uses a non-default session, call
``Model.objects.using(session)`` on managers the same way as other services
(see :doc:`/overview/services`).

CloudWatchMetric
----------------

A :py:class:`~botocraft.services.cloudwatch.CloudWatchMetric` represents one
metric time series: ``Namespace``, ``MetricName``, and optional
``Dimensions``. The model is read-only at the AWS resource level (metrics are
discovered with ``ListMetrics``). To write datapoints, call
:py:meth:`~botocraft.services.cloudwatch.CloudWatchMetric.publish`.

Search for metrics
~~~~~~~~~~~~~~~~~~

Use two complementary patterns depending on how specific the identity is.

**Broad search** — list with AWS namespace/name filters, then narrow in memory
if needed:

.. code-block:: python

    metrics = CloudWatchMetric.objects.list(
        Namespace="Custom/App",
        MetricName="RequestCount",
    )

    prod = [
        metric
        for metric in metrics
        if any(
            dimension.Name == "Environment" and dimension.Value == "prod"
            for dimension in (metric.Dimensions or [])
        )
    ]

``ListMetrics`` can return metrics that match a dimension *name* but carry
additional dimensions. Botocraft's exact ``get`` (below) is stricter.

**Exact identity** — :py:meth:`~botocraft.services.cloudwatch.CloudWatchMetricManager.get`
pages through ``ListMetrics`` and matches namespace, name, and the full
dimension set client-side:

.. code-block:: python

    metric = CloudWatchMetric.objects.get(
        Namespace="Custom/App",
        MetricName="RequestCount",
        Dimensions=[CloudWatchDimension(Name="Environment", Value="prod")],
    )

Pitfalls:

* ``get`` requires at least one of ``Namespace``, ``MetricName``, or
  ``Dimensions`` (or pass a metric model whose fields define the lookup).
* More than one match raises :py:exc:`ValueError`; add dimensions or tighten
  filters.
* ``get`` returns ``None`` when no series matches.

Publish datapoints
~~~~~~~~~~~~~~~~~~

Construct or resolve a metric, then publish one or more datapoints. The manager
fills in ``MetricName`` and ``Dimensions`` on each ``MetricData`` entry when
they are omitted; ``Namespace`` must be set on the model.

.. code-block:: python

    metric = CloudWatchMetric(
        Namespace="Custom/App",
        MetricName="RequestCount",
        Dimensions=[CloudWatchDimension(Name="Environment", Value="prod")],
    )
    metric.publish(
        MetricData=[
            {
                "Value": 1.0,
                "Timestamp": datetime.now(tz=UTC),
                "Unit": "Count",
            }
        ],
    )

For sub-minute custom metrics, include AWS ``StorageResolution`` in the payload
(``1`` for high-resolution storage). Botocraft forwards ``MetricData`` fields
to ``PutMetricData`` as-is.

Retrieve metric data
~~~~~~~~~~~~~~~~~~~~

Botocraft exposes two query paths. Pick based on the statistics you need.

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - AWS API
     - Botocraft method
     - Prefer when
   * - ``GetMetricData``
     - :py:meth:`~botocraft.services.cloudwatch.CloudWatchMetric.get_data`
     - Default for new code; extended percentiles (``p99``, ``p95.0``); typed
       ``Period`` and ``Stat`` (:data:`~botocraft.mixins.cloudwatch.CloudWatchGetDataPeriod`,
       :data:`~botocraft.mixins.cloudwatch.CloudWatchGetDataStat`)
   * - ``GetMetricStatistics``
     - :py:meth:`~botocraft.services.cloudwatch.CloudWatchMetric.get_statistics`
     - Multiple classic statistics in one call (``Statistics=[...]`` or
       ``ExtendedStatistics=[...]``); ``Period`` is a plain integer in seconds

Choosing ``Period``
^^^^^^^^^^^^^^^^^^^

* Match chart granularity to the time window: 5–15 minute charts often use
  ``300``–``900`` seconds; hourly views use ``3600``.
* For :py:meth:`~botocraft.services.cloudwatch.CloudWatchMetric.get_data`,
  ``Period`` must be one of ``1``, ``5``, ``10``, ``20``, ``30``, ``60``,
  ``120``, ``300``, ``600``, ``900``, ``1800``, ``3600``, ``10800``, ``21600``,
  ``43200``, or ``86400`` (see
  :data:`~botocraft.mixins.cloudwatch.CloudWatchGetDataPeriod`).
* Keep roughly under CloudWatch's datapoint limit per request (~1440 points):
  increase ``Period`` when ``EndTime - StartTime`` is large.
* High-resolution custom metrics (``StorageResolution`` of ``1`` on publish)
  support finer ``Period`` values on ``get_statistics`` (``1``, ``5``, ``10``,
  ``20``, ``30``, or multiples of ``60``).

Choosing ``Stat``
^^^^^^^^^^^^^^^^^

* Utilization-style gauges: ``Average`` (for example CPU), ``Maximum`` for
  spikes.
* Counters and throughput: ``Sum`` or ``SampleCount``.
* Latency SLOs: extended percentiles via ``get_data``, for example ``Stat="p99"``
  or ``Stat="p95.0"``.
* On ``get_statistics``, pass ``Statistics=["Average", "Sum"]`` **or**
  ``ExtendedStatistics=["p95.0"]``, not both omitted.

Choosing ``Unit``
^^^^^^^^^^^^^^^^^

* Omit ``Unit`` (default ``None``) when unsure; CloudWatch may return data stored
  under any unit.
* When publishing and querying must align, set the same standard unit on publish
  and on read (for example ``Count``, ``Seconds``, ``Percent``, ``Bytes``,
  ``Bytes/Second``, or ``None``). See
  :data:`~botocraft.mixins.cloudwatch.CloudWatchMetricUnit`.
* A mismatched unit filter often yields empty results; CloudWatch does not
  convert units for you.

``get_data`` example
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    end = datetime.now(tz=UTC)
    start = end - timedelta(hours=1)

    results = metric.get_data(
        StartTime=start,
        EndTime=end,
        Period=60,
        Stat="Average",
        Unit="Count",
    )

    if results:
        series = results[0]
        timestamps = series.get("Timestamps", [])
        values = series.get("Values", [])

``get_statistics`` example
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    datapoints = metric.get_statistics(
        StartTime=start,
        EndTime=end,
        Period=60,
        Statistics=["Average", "Sum"],
    )

Widget images
^^^^^^^^^^^^^

:py:meth:`~botocraft.services.cloudwatch.CloudWatchMetric.widget_image` calls
``GetMetricWidgetImage`` with dashboard widget JSON and returns raw image bytes.
Use this when you need a PNG snapshot without building a full dashboard resource
in code.

Bridge metrics to metric streams
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:py:meth:`~botocraft.services.cloudwatch.CloudWatchMetric.to_stream_include_filter`
and
:py:meth:`~botocraft.services.cloudwatch.CloudWatchMetric.to_stream_statistics_metric`
build stream filter objects from a metric's namespace and name (see metric
streams below).

CloudWatchMetricStream
----------------------

A :py:class:`~botocraft.services.cloudwatch.CloudWatchMetricStream` forwards
selected account metrics to a Kinesis Data Firehose delivery stream (often S3,
or a third-party destination configured on Firehose). Botocraft manages stream
configuration and start/stop; reading records from the destination is outside
the CloudWatch API (see `Consume stream data`_).

Prerequisites (Terraform)
~~~~~~~~~~~~~~~~~~~~~~~~~

Create Firehose, IAM, and the metric stream in infrastructure code. The stream
role must trust ``streams.metrics.cloudwatch.amazonaws.com`` and allow Firehose
writes. Example skeleton (replace bucket, account, and names):

.. code-block:: terraform

    resource "aws_s3_bucket" "metric_stream" {
      bucket = "my-account-metric-stream"
    }

    resource "aws_iam_role" "metric_stream" {
      name = "MetricStreamRole"

      assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
          Effect = "Allow"
          Principal = { Service = "streams.metrics.cloudwatch.amazonaws.com" }
          Action = "sts:AssumeRole"
        }]
      })
    }

    resource "aws_iam_role_policy" "metric_stream_firehose" {
      name = "MetricStreamFirehosePut"
      role = aws_iam_role.metric_stream.id

      policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
          Effect   = "Allow"
          Action   = ["firehose:PutRecord", "firehose:PutRecordBatch"]
          Resource = aws_kinesis_firehose_delivery_stream.primary.arn
        }]
      })
    }

    resource "aws_iam_role" "firehose_s3" {
      name = "FirehoseS3Role"
      # Trust firehose.amazonaws.com and attach s3:PutObject on the bucket.
    }

    resource "aws_kinesis_firehose_delivery_stream" "primary" {
      name        = "primary"
      destination = "extended_s3"

      extended_s3_configuration {
        role_arn   = aws_iam_role.firehose_s3.arn
        bucket_arn = aws_s3_bucket.metric_stream.arn
      }
    }

    resource "aws_cloudwatch_metric_stream" "primary" {
      name          = "primary"
      firehose_arn  = aws_kinesis_firehose_delivery_stream.primary.arn
      role_arn      = aws_iam_role.metric_stream.arn
      output_format = "json"

      include_filter {
        namespace = "Custom/App"
      }
    }

Complete the Firehose S3 role trust policy and bucket policy in your own module;
the snippet only shows how ARNs connect. Wire ARNs from Terraform into botocraft
when creating or updating streams in application code.

Create and configure with botocraft
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    metric = CloudWatchMetric.objects.get(
        Namespace="Custom/App",
        MetricName="RequestCount",
        Dimensions=[CloudWatchDimension(Name="Environment", Value="prod")],
    )

    stream = CloudWatchMetricStream(
        Name="primary",
        FirehoseArn=(
            "arn:aws:firehose:us-west-2:123456789012:deliverystream/primary"
        ),
        OutputFormat="json",
    )

    CloudWatchMetricStream.objects.create(
        stream,
        RoleArn="arn:aws:iam::123456789012:role/MetricStreamRole",
        IncludeFilters=[metric.to_stream_include_filter()],
        StatisticsConfigurations=[
            CloudWatchMetricStreamStatisticsConfiguration(
                IncludeMetrics=[metric.to_stream_statistics_metric()],
                AdditionalStatistics=["p99"],
            )
        ],
    )

By default, streams emit ``MIN``, ``MAX``, ``SUM``, and ``SAMPLECOUNT`` for each
metric. ``StatisticsConfigurations`` adds statistics such as ``p99`` for listed
metrics.

Start and stop streaming
~~~~~~~~~~~~~~~~~~~~~~~~

Start and stop are manager methods on
:py:class:`~botocraft.services.cloudwatch.CloudWatchMetricStreamManager`:

.. code-block:: python

    CloudWatchMetricStream.objects.start("primary")
    CloudWatchMetricStream.objects.stop("primary")

    stream = CloudWatchMetricStream.objects.get("primary")
    if stream is not None:
        print(stream.State)  # "running" or "stopped"

Inspect ``State`` after operations; delivery to Firehose may lag slightly after
``start``.

Consume stream data
~~~~~~~~~~~~~~~~~~~

Botocraft does not read Firehose or S3 payloads. After ``start``:

1. CloudWatch writes metric records to the configured Firehose delivery stream.
2. Firehose lands objects in S3 (or another destination you configured).
3. Consume with the AWS SDK for that destination.

**S3 destination** — list and read objects under the Firehose prefix:

.. code-block:: python

    import boto3

    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket="my-account-metric-stream", Prefix=""):
        for obj in page.get("Contents", []):
            body = s3.get_object(Bucket="my-account-metric-stream", Key=obj["Key"])[
                "Body"
            ].read()
            # Parse JSON (output_format = "json") or OpenTelemetry payloads

**Output format** — ``OutputFormat`` on the stream is ``json``,
``opentelemetry0.7``, or ``opentelemetry1.0``. Pick parsers accordingly.

**Statistics in the payload** — expect ``MIN``, ``MAX``, ``SUM``, and
``SAMPLECOUNT`` unless you added ``StatisticsConfigurations`` on create/update.

Related CloudWatch resources
----------------------------

These primaries share the same service module and are documented in the API
reference. Overview pages may be added later; until then use
:doc:`/api/services/cloudwatch`.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Model
     - Typical use
   * - :py:class:`~botocraft.services.cloudwatch.MetricAlarm`
     - Threshold alarms; ``set_state``, ``enable_actions``, ``describe_history``
   * - :py:class:`~botocraft.services.cloudwatch.CompositeAlarm`
     - Alarm combinations across child alarms
   * - :py:class:`~botocraft.services.cloudwatch.CloudWatchDashboard`
     - Dashboard bodies as JSON via ``DashboardBody``
   * - :py:class:`~botocraft.services.cloudwatch.CloudWatchInsightRule`
     - Contributor insights; customer-managed rules in ``list``/``get``
   * - :py:class:`~botocraft.services.cloudwatch.CloudWatchAnomalyDetector`
     - Anomaly bands; exact-match ``get`` and ``delete``
   * - :py:class:`~botocraft.services.cloudwatch.AlarmMuteRule`
     - Scheduled alarm muting
   * - :py:class:`~botocraft.services.cloudwatch.OTelEnrichmentStatus`
     - Account-level OpenTelemetry enrichment ``start``/``stop``/``get``

The same :py:class:`~botocraft.services.cloudwatch.CloudWatchMetric` APIs apply
to AWS service namespaces (for example ``AWS/EC2``, ``AWS/RDS``) when listing and
querying built-in metrics.

Possible API improvements
-------------------------

The following are not implemented today but would make the CloudWatch module
easier to use:

* **Instance ``start``/``stop`` on streams** — mirror
  :py:meth:`~botocraft.services.cloudwatch.CloudWatchMetric.publish` so
  ``stream.start()`` is available without going through ``objects``.
* **Paginated ``list_metric_streams``** — today ``list`` is a single API call;
  large accounts may need pagination.
* **Publish helper** — build ``MetricData`` dicts with a default UTC timestamp
  and optional ``Unit``/``StorageResolution``.
* **``get_data`` result helper** — return ``{timestamps, values}`` for the
  default query id instead of raw ``MetricDataResults`` dicts.
* **``search`` alias on metrics** — document-friendly wrapper over ``list`` plus
  exact-dimension filtering.
* **Metric-to-alarm snippet helper** — emit namespace/name/dimensions compatible
  with alarm creation.

See also
--------

* :doc:`/overview/services` — managers and ``objects``
* :doc:`/overview/queryset` — filtering listed results
* :doc:`/api/services/cloudwatch` — generated model and manager reference
