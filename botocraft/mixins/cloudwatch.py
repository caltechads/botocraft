"""Handwritten helpers for generated CloudWatch managers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, cast

if TYPE_CHECKING:
    from datetime import datetime

#: Aggregation periods accepted by :py:meth:`CloudWatchMetricManagerMixin.get_data`.
CloudWatchGetDataPeriod = Literal[
    1,
    5,
    10,
    20,
    30,
    60,
    120,
    300,
    600,
    900,
    1800,
    3600,
    10800,
    21600,
    43200,
    86400,
]
#: Standard statistics accepted by :py:meth:`CloudWatchMetricManagerMixin.get_data`.
CloudWatchStandardStat = Literal[
    "SampleCount",
    "Average",
    "Sum",
    "Minimum",
    "Maximum",
]
#: Extended percentile statistics (``p`` prefix) for ``get_data``.
CloudWatchExtendedPercentileStat = Literal[
    "p0",
    "p1",
    "p2",
    "p3",
    "p4",
    "p5",
    "p6",
    "p7",
    "p8",
    "p9",
    "p10",
    "p11",
    "p12",
    "p13",
    "p14",
    "p15",
    "p16",
    "p17",
    "p18",
    "p19",
    "p20",
    "p21",
    "p22",
    "p23",
    "p24",
    "p25",
    "p26",
    "p27",
    "p28",
    "p29",
    "p30",
    "p31",
    "p32",
    "p33",
    "p34",
    "p35",
    "p36",
    "p37",
    "p38",
    "p39",
    "p40",
    "p41",
    "p42",
    "p43",
    "p44",
    "p45",
    "p46",
    "p47",
    "p48",
    "p49",
    "p50",
    "p51",
    "p52",
    "p53",
    "p54",
    "p55",
    "p56",
    "p57",
    "p58",
    "p59",
    "p60",
    "p61",
    "p62",
    "p63",
    "p64",
    "p65",
    "p66",
    "p67",
    "p68",
    "p69",
    "p70",
    "p71",
    "p72",
    "p73",
    "p74",
    "p75",
    "p76",
    "p77",
    "p78",
    "p79",
    "p80",
    "p81",
    "p82",
    "p83",
    "p84",
    "p85",
    "p86",
    "p87",
    "p88",
    "p89",
    "p90",
    "p91",
    "p92",
    "p93",
    "p94",
    "p95",
    "p96",
    "p97",
    "p98",
    "p99",
    "p100",
    "p0.0",
    "p1.0",
    "p5.0",
    "p10.0",
    "p25.0",
    "p50.0",
    "p75.0",
    "p90.0",
    "p95.0",
    "p99.0",
    "p99.9",
    "p99.99",
    "p100.0",
]
#: Statistics accepted by :py:meth:`CloudWatchMetricManagerMixin.get_data`.
CloudWatchGetDataStat = CloudWatchStandardStat | CloudWatchExtendedPercentileStat
#: Standard metric units accepted by CloudWatch metric query helpers.
CloudWatchMetricUnit = Literal[
    "Seconds",
    "Microseconds",
    "Milliseconds",
    "Bytes",
    "Kilobytes",
    "Megabytes",
    "Gigabytes",
    "Terabytes",
    "Bits",
    "Kilobits",
    "Megabits",
    "Gigabits",
    "Terabits",
    "Percent",
    "Count",
    "Bytes/Second",
    "Kilobytes/Second",
    "Megabytes/Second",
    "Gigabytes/Second",
    "Terabytes/Second",
    "Bits/Second",
    "Kilobits/Second",
    "Megabits/Second",
    "Gigabits/Second",
    "Terabits/Second",
    "Count/Second",
    "None",
]

from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.cloudwatch import (
        CloudWatchAnomalyDetector,
        CloudWatchInsightRule,
        CloudWatchMetric,
        CloudWatchMetricStreamFilter,
        MetricStreamStatisticsMetric,
    )


def _normalize_payload(value: Any) -> Any:
    """
    Normalize Botocraft models, lists, and dictionaries for equality checks.

    Args:
        value: Arbitrary nested detector payload data.

    Returns:
        A plain-Python representation suitable for exact comparisons.

    """
    if hasattr(value, "model_dump"):
        return _normalize_payload(value.model_dump(exclude_none=True))
    if isinstance(value, list):
        return [_normalize_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _normalize_payload(item)
            for key, item in value.items()
            if item is not None
        }
    return value


class CloudWatchInsightRuleManagerMixin:
    """
    Read helpers for customer-managed CloudWatch Insight Rules.

    CloudWatch does not expose a single-rule describe operation or a server-side
    rule-name filter for ``DescribeInsightRules``. This mixin keeps the public
    Botocraft contract honest by paging through the real list operation and then
    filtering in memory, while excluding managed rules that belong to the
    separate managed-rule workflow.
    """

    def list(self) -> PrimaryBoto3ModelQuerySet:
        """
        Return customer-managed Insight Rules visible to the current session.

        Returns:
            A queryset of
            :py:class:`botocraft.services.cloudwatch.CloudWatchInsightRule`
            objects.

        Side Effects:
            Performs paginated ``DescribeInsightRules`` API calls.

        """
        from botocraft.services.cloudwatch import CloudWatchInsightRule

        paginator = self.client.get_paginator("describe_insight_rules")  # type: ignore[attr-defined]
        rules: list[CloudWatchInsightRule] = []
        for response in paginator.paginate():
            for payload in response.get("InsightRules", []):
                if payload.get("ManagedRule"):
                    continue
                rules.append(CloudWatchInsightRule(**payload))
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", rules))
        self.sessionize(query_set)  # type: ignore[attr-defined]
        return query_set

    def get(self, Name: str) -> CloudWatchInsightRule | None:  # noqa: N803
        """
        Return one customer-managed Insight Rule by name.

        Args:
            Name: Insight Rule name to match.

        Returns:
            The matching
            :py:class:`botocraft.services.cloudwatch.CloudWatchInsightRule`, or
            ``None`` when no customer-managed rule matches.

        Side Effects:
            Performs ``DescribeInsightRules`` API calls and follows pagination
            manually until a matching rule is found or the result set is
            exhausted.

        """
        from botocraft.services.cloudwatch import CloudWatchInsightRule

        next_token: str | None = None
        while True:
            args: dict[str, Any] = {}
            if next_token is not None:
                args["NextToken"] = next_token
            response = self.client.describe_insight_rules(  # type: ignore[attr-defined]
                **args
            )
            for payload in response.get("InsightRules", []):
                if payload.get("ManagedRule"):
                    continue
                if payload.get("Name") == Name:
                    insight_rule = CloudWatchInsightRule(**payload)
                    self.sessionize(insight_rule)  # type: ignore[attr-defined]
                    return insight_rule
            next_token = response.get("NextToken")
            if next_token is None:
                break
        return None


class CloudWatchAnomalyDetectorManagerMixin:
    """
    Exact-match getter helpers for CloudWatch anomaly detectors.

    ``DescribeAnomalyDetectors`` supports only partial server-side filtering, so
    Botocraft has to finish matching detector identity client-side when callers
    need a single detector.
    """

    def get(  # noqa: PLR0913
        self,
        *,
        Namespace: str | None = None,  # noqa: N803
        MetricName: str | None = None,  # noqa: N803
        Dimensions: list[Any] | None = None,  # noqa: N803
        AnomalyDetectorTypes: list[str] | None = None,  # noqa: N803
        Stat: str | None = None,  # noqa: N803
        SingleMetricAnomalyDetector: Any | None = None,  # noqa: N803
        MetricMathAnomalyDetector: Any | None = None,  # noqa: N803
    ) -> CloudWatchAnomalyDetector | None:
        """
        Return one anomaly detector that exactly matches the supplied identity.

        Keyword Args:
            Namespace: Metric namespace forwarded to ``DescribeAnomalyDetectors``.
            MetricName: Metric name forwarded to ``DescribeAnomalyDetectors``.
            Dimensions: Dimension filters forwarded to ``DescribeAnomalyDetectors``.
            AnomalyDetectorTypes: Detector-type filters forwarded to
                ``DescribeAnomalyDetectors``.
            Stat: Exact statistic to match after the describe call.
            SingleMetricAnomalyDetector: Exact nested single-metric detector shape
                to match after the describe call.
            MetricMathAnomalyDetector: Exact nested metric-math detector shape to
                match after the describe call.

        Raises:
            ValueError: No narrowing filters were provided, or the supplied
                filters still match more than one detector.

        Returns:
            The matching
            :py:class:`botocraft.services.cloudwatch.CloudWatchAnomalyDetector`,
            or ``None`` when no detector matches.

        Side Effects:
            Performs ``DescribeAnomalyDetectors`` API calls and follows
            pagination while applying client-side exact matching.

        """
        from botocraft.services.cloudwatch import CloudWatchAnomalyDetector

        if not any(
            [
                Namespace,
                MetricName,
                Dimensions,
                AnomalyDetectorTypes,
                Stat,
                SingleMetricAnomalyDetector,
                MetricMathAnomalyDetector,
            ]
        ):
            msg = (
                "CloudWatchAnomalyDetectorManager.get requires at least one "
                "filter to avoid an unscoped anomaly-detector scan."
            )
            raise ValueError(msg)

        normalized_dimensions = _normalize_payload(Dimensions)
        normalized_single_metric = _normalize_payload(SingleMetricAnomalyDetector)
        normalized_metric_math = _normalize_payload(MetricMathAnomalyDetector)
        request_args: dict[str, Any] = {
            "Namespace": self.serialize(Namespace),  # type: ignore[attr-defined]
            "MetricName": self.serialize(MetricName),  # type: ignore[attr-defined]
            "Dimensions": self.serialize(Dimensions),  # type: ignore[attr-defined]
            "AnomalyDetectorTypes": self.serialize(AnomalyDetectorTypes),  # type: ignore[attr-defined]
        }

        matches: list[CloudWatchAnomalyDetector] = []
        next_token: str | None = None
        while True:
            if next_token is not None:
                request_args["NextToken"] = next_token
            else:
                request_args.pop("NextToken", None)
            response = self.client.describe_anomaly_detectors(  # type: ignore[attr-defined]
                **{
                    key: value
                    for key, value in request_args.items()
                    if value is not None
                }
            )
            for payload in response.get("AnomalyDetectors", []):
                anomaly_detector = CloudWatchAnomalyDetector(**payload)
                if (
                    normalized_dimensions is not None
                    and _normalize_payload(anomaly_detector.Dimensions)
                    != normalized_dimensions
                ):
                    continue
                if Stat is not None and anomaly_detector.Stat != Stat:
                    continue
                if (
                    normalized_single_metric is not None
                    and _normalize_payload(anomaly_detector.SingleMetricAnomalyDetector)
                    != normalized_single_metric
                ):
                    continue
                if (
                    normalized_metric_math is not None
                    and _normalize_payload(anomaly_detector.MetricMathAnomalyDetector)
                    != normalized_metric_math
                ):
                    continue
                matches.append(anomaly_detector)
            next_token = response.get("NextToken")
            if next_token is None:
                break

        if not matches:
            return None
        if len(matches) > 1:
            msg = (
                "CloudWatch anomaly-detector filters matched more than one "
                "detector. Add narrower identity fields such as Stat, "
                "SingleMetricAnomalyDetector, or MetricMathAnomalyDetector."
            )
            raise ValueError(msg)
        self.sessionize(matches[0])  # type: ignore[attr-defined]
        return matches[0]

    def delete(self, model: CloudWatchAnomalyDetector) -> None:
        """
        Delete the anomaly detector identified by the supplied model.

        Args:
            model: The
                :py:class:`botocraft.services.cloudwatch.CloudWatchAnomalyDetector`
                to delete.

        Side Effects:
            Performs a ``DeleteAnomalyDetector`` API call.

        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        args = {
            "Namespace": data.get("Namespace"),
            "MetricName": data.get("MetricName"),
            "Dimensions": data.get("Dimensions"),
            "Stat": data.get("Stat"),
            "SingleMetricAnomalyDetector": data.get("SingleMetricAnomalyDetector"),
            "MetricMathAnomalyDetector": data.get("MetricMathAnomalyDetector"),
        }
        self.client.delete_anomaly_detector(  # type: ignore[attr-defined]
            **{key: value for key, value in args.items() if value is not None}
        )


def _metric_identity(
    *,
    namespace: str | None,
    metric_name: str | None,
    dimensions: list[Any] | None,
) -> dict[str, Any]:
    """
    Build a normalized metric identity payload for exact matching.

    Keyword Args:
        namespace: Metric namespace.
        metric_name: Metric name.
        dimensions: Metric dimensions.

    Returns:
        A plain dictionary suitable for equality checks.

    """
    normalized_dimensions = _normalize_payload(dimensions)
    if isinstance(normalized_dimensions, list):
        normalized_dimensions = sorted(
            normalized_dimensions,
            key=lambda item: item.get("Name", ""),
        )
    return {
        "Namespace": namespace,
        "MetricName": metric_name,
        "Dimensions": normalized_dimensions or [],
    }


def _metrics_match(
    candidate: dict[str, Any],
    *,
    namespace: str | None,
    metric_name: str | None,
    dimensions: list[Any] | None,
) -> bool:
    """
    Return whether a ``ListMetrics`` payload matches the supplied identity.

    Args:
        candidate: One metric payload from ``ListMetrics``.

    Keyword Args:
        namespace: Expected namespace, if provided.
        metric_name: Expected metric name, if provided.
        dimensions: Expected dimensions, if provided.

    Returns:
        ``True`` when the candidate matches all supplied identity fields.

    """
    if namespace is not None and candidate.get("Namespace") != namespace:
        return False
    if metric_name is not None and candidate.get("MetricName") != metric_name:
        return False
    if dimensions is not None:
        return _metric_identity(
            namespace=candidate.get("Namespace"),
            metric_name=candidate.get("MetricName"),
            dimensions=candidate.get("Dimensions"),
        ) == _metric_identity(
            namespace=namespace,
            metric_name=metric_name,
            dimensions=dimensions,
        )
    return True


class CloudWatchMetricModelMixin:
    """
    Convenience helpers for metric-stream filter construction.

    These helpers translate a metric identity into stream filter shapes. They do
    not create or manage metric streams themselves.
    """

    def to_stream_include_filter(self) -> CloudWatchMetricStreamFilter:
        """
        Build a metric-stream include filter for this metric's namespace and name.

        Returns:
            A
            :py:class:`botocraft.services.cloudwatch.CloudWatchMetricStreamFilter`
            suitable for ``IncludeFilters`` on a metric stream.

        Raises:
            ValueError: ``Namespace`` or ``MetricName`` is missing on the model.

        """
        from botocraft.services.cloudwatch import CloudWatchMetricStreamFilter

        namespace = getattr(self, "Namespace", None)
        metric_name = getattr(self, "MetricName", None)
        if not namespace or not metric_name:
            msg = (
                "CloudWatchMetric.to_stream_include_filter requires Namespace "
                "and MetricName."
            )
            raise ValueError(msg)
        return CloudWatchMetricStreamFilter(
            Namespace=namespace,
            MetricNames=[metric_name],
        )

    def to_stream_statistics_metric(self) -> MetricStreamStatisticsMetric:
        """
        Build a statistics-configuration metric entry for this metric.

        Returns:
            A
            :py:class:`botocraft.services.cloudwatch.MetricStreamStatisticsMetric`
            for ``StatisticsConfigurations``.

        Raises:
            ValueError: ``Namespace`` or ``MetricName`` is missing on the model.

        """
        from botocraft.services.cloudwatch import MetricStreamStatisticsMetric

        namespace = getattr(self, "Namespace", None)
        metric_name = getattr(self, "MetricName", None)
        if not namespace or not metric_name:
            msg = (
                "CloudWatchMetric.to_stream_statistics_metric requires "
                "Namespace and MetricName."
            )
            raise ValueError(msg)
        return MetricStreamStatisticsMetric(
            Namespace=namespace,
            MetricName=metric_name,
        )


class CloudWatchMetricManagerMixin:
    """
    Metric identity and datapoint helpers for CloudWatch custom metrics.

    CloudWatch exposes metric discovery and datapoint APIs against metric
    identity rather than a single-resource describe operation, so ``get`` and
    several write/read helpers are implemented here.
    """

    def get(
        self,
        model: CloudWatchMetric | None = None,
        *,
        Namespace: str | None = None,  # noqa: N803
        MetricName: str | None = None,  # noqa: N803
        Dimensions: list[Any] | None = None,  # noqa: N803
    ) -> CloudWatchMetric | None:
        """
        Return one metric that exactly matches the supplied identity.

        Args:
            model: Optional
                :py:class:`botocraft.services.cloudwatch.CloudWatchMetric` whose
                identity fields should be used for the lookup.

        Keyword Args:
            Namespace: Metric namespace to match.
            MetricName: Metric name to match.
            Dimensions: Metric dimensions to match exactly.

        Raises:
            ValueError: No narrowing filters were provided, or the supplied
                filters still match more than one metric.

        Returns:
            The matching
            :py:class:`botocraft.services.cloudwatch.CloudWatchMetric`, or
            ``None`` when no metric matches.

        Side Effects:
            Performs paginated ``ListMetrics`` API calls.

        """
        namespace = Namespace
        metric_name = MetricName
        dimensions = Dimensions
        if model is not None:
            namespace = model.Namespace
            metric_name = model.MetricName
            dimensions = model.Dimensions

        if not any([namespace, metric_name, dimensions]):
            msg = (
                "CloudWatchMetricManager.get requires a metric model or at "
                "least one identity filter."
            )
            raise ValueError(msg)

        matches = self._list_metrics_matching(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
        )
        if not matches:
            return None
        if len(matches) > 1:
            msg = (
                "CloudWatch metric filters matched more than one metric. Add "
                "Namespace, MetricName, and Dimensions to narrow the match."
            )
            raise ValueError(msg)
        self.sessionize(matches[0])  # type: ignore[attr-defined]
        return matches[0]

    def publish(
        self,
        model: CloudWatchMetric,
        MetricData: list[Any],  # noqa: N803
    ) -> None:
        """
        Publish datapoints for the supplied metric identity.

        Args:
            model: The
                :py:class:`botocraft.services.cloudwatch.CloudWatchMetric`
                whose ``Namespace``, ``MetricName``, and ``Dimensions`` identify
                the series.
            MetricData: Datapoint payloads accepted by ``PutMetricData``.

        Raises:
            ValueError: The model is missing ``Namespace``.

        Side Effects:
            Performs a ``PutMetricData`` API call.

        """
        if not model.Namespace:
            msg = "CloudWatchMetricManager.publish requires model.Namespace."
            raise ValueError(msg)

        metric_data: list[dict[str, Any]] = []
        for entry in MetricData:
            payload = (
                entry.model_dump(exclude_none=True)
                if hasattr(entry, "model_dump")
                else dict(entry)
            )
            payload.setdefault("MetricName", model.MetricName)
            if model.Dimensions and "Dimensions" not in payload:
                payload["Dimensions"] = [
                    dimension.model_dump(exclude_none=True)
                    if hasattr(dimension, "model_dump")
                    else dimension
                    for dimension in model.Dimensions
                ]
            metric_data.append(payload)

        self.client.put_metric_data(  # type: ignore[attr-defined]
            Namespace=model.Namespace,
            MetricData=self.serialize(metric_data),  # type: ignore[attr-defined]
        )

    def get_data(  # noqa: PLR0913
        self,
        model: CloudWatchMetric,
        StartTime: datetime,  # noqa: N803
        EndTime: datetime,  # noqa: N803
        Period: CloudWatchGetDataPeriod,  # noqa: N803
        Stat: CloudWatchGetDataStat,  # noqa: N803
        Unit: CloudWatchMetricUnit | None = None,  # noqa: N803
        ScanBy: str | None = None,  # noqa: N803
    ) -> list[Any]:
        """
        Retrieve metric data for one metric identity via ``GetMetricData``.

        Args:
            model: The metric identity to query.

        Keyword Args:
            StartTime: Inclusive query start time.
            EndTime: Exclusive query end time.
            Period: Aggregation period in seconds. Must be one of ``1``, ``5``,
                ``10``, ``20``, ``30``, ``60``, ``120``, ``300``, ``600``, ``900``,
                ``1800``, ``3600``, ``10800``, ``21600``, ``43200``, or ``86400``.
            Stat: Statistic for the query. Use ``SampleCount``, ``Average``,
                ``Sum``, ``Minimum``, or ``Maximum`` for standard statistics, or
                an extended percentile such as ``p99`` or ``p95.0`` (``p0``
                through ``p100``, plus common decimal forms like ``p99.9``).
            Unit: Optional unit filter. When omitted, CloudWatch may return data
                stored under any unit. When set, must be a standard unit such as
                ``Seconds``, ``Count``, ``Percent``, ``Bytes``, or ``Bytes/Second``
                (see :data:`~botocraft.mixins.cloudwatch.CloudWatchMetricUnit`).
            ScanBy: Optional scan direction: ``TimestampDescending`` or
                ``TimestampAscending``.

        Returns:
            ``MetricDataResults`` entries from the AWS response.

        Side Effects:
            Performs a ``GetMetricData`` API call.

        """
        from botocraft.services.cloudwatch import (
            CloudWatchMetricDataQuery,
            CloudWatchMetricStat,
        )

        metric_stat = CloudWatchMetricStat(
            Metric=model,
            Period=Period,
            Stat=Stat,
            Unit=Unit,
        )
        query = CloudWatchMetricDataQuery(
            Id="m1",
            ReturnData=True,
            MetricStat=metric_stat,
        )
        args: dict[str, Any] = {
            "MetricDataQueries": [query.model_dump(exclude_none=True, by_alias=True)],
            "StartTime": StartTime,
            "EndTime": EndTime,
        }
        if ScanBy is not None:
            args["ScanBy"] = ScanBy

        response = self.client.get_metric_data(  # type: ignore[attr-defined]
            **self.serialize(args)  # type: ignore[attr-defined]
        )
        return response.get("MetricDataResults", [])

    def get_statistics(  # noqa: PLR0913
        self,
        model: CloudWatchMetric,
        StartTime: datetime,  # noqa: N803
        EndTime: datetime,  # noqa: N803
        Period: int,  # noqa: N803
        Statistics: list[str] | None = None,  # noqa: N803
        ExtendedStatistics: list[str] | None = None,  # noqa: N803
        Unit: CloudWatchMetricUnit | None = None,  # noqa: N803
    ) -> list[Any]:
        """
        Retrieve aggregated datapoints via ``GetMetricStatistics``.

        Args:
            model: The metric identity to query.

        Keyword Args:
            StartTime: Inclusive query start time.
            EndTime: Exclusive query end time.
            Period: Aggregation period in seconds.
            Statistics: Optional classic statistics list.
            ExtendedStatistics: Optional extended statistics list.
            Unit: Optional unit filter. When omitted, CloudWatch may return data
                stored under any unit. When set, must be a standard unit (see
                :data:`~botocraft.mixins.cloudwatch.CloudWatchMetricUnit`).

        Raises:
            ValueError: The model is missing ``Namespace`` or ``MetricName``.

        Returns:
            ``Datapoints`` entries from the AWS response.

        Side Effects:
            Performs a ``GetMetricStatistics`` API call.

        """
        if not model.Namespace or not model.MetricName:
            msg = (
                "CloudWatchMetricManager.get_statistics requires model "
                "Namespace and MetricName."
            )
            raise ValueError(msg)

        args: dict[str, Any] = {
            "Namespace": model.Namespace,
            "MetricName": model.MetricName,
            "Dimensions": [
                dimension.model_dump(exclude_none=True)
                if hasattr(dimension, "model_dump")
                else dimension
                for dimension in (model.Dimensions or [])
            ],
            "StartTime": StartTime,
            "EndTime": EndTime,
            "Period": Period,
        }
        if Statistics is not None:
            args["Statistics"] = Statistics
        if ExtendedStatistics is not None:
            args["ExtendedStatistics"] = ExtendedStatistics
        if Unit is not None:
            args["Unit"] = Unit

        response = self.client.get_metric_statistics(  # type: ignore[attr-defined]
            **self.serialize(args)  # type: ignore[attr-defined]
        )
        return response.get("Datapoints", [])

    def widget_image(
        self,
        MetricWidget: str,  # noqa: N803
    ) -> bytes:
        """
        Render a metric widget image via ``GetMetricWidgetImage``.

        Keyword Args:
            MetricWidget: Dashboard widget definition JSON.

        Returns:
            Raw image bytes from ``MetricWidgetImage``.

        Side Effects:
            Performs a ``GetMetricWidgetImage`` API call.

        """
        response = self.client.get_metric_widget_image(  # type: ignore[attr-defined]
            MetricWidget=MetricWidget
        )
        metric_widget_image = response.get("MetricWidgetImage")
        if isinstance(metric_widget_image, bytes):
            return metric_widget_image
        if isinstance(metric_widget_image, str):
            return metric_widget_image.encode("utf-8")
        return b""

    def _list_metrics_matching(
        self,
        *,
        Namespace: str | None = None,  # noqa: N803
        MetricName: str | None = None,  # noqa: N803
        Dimensions: list[Any] | None = None,  # noqa: N803
    ) -> list[CloudWatchMetric]:
        """
        Return metrics from ``ListMetrics`` that match the supplied identity.

        Keyword Args:
            Namespace: Optional namespace filter forwarded to AWS.
            MetricName: Optional metric-name filter forwarded to AWS.
            Dimensions: Optional exact dimension set matched client-side.

        Returns:
            Matching
            :py:class:`botocraft.services.cloudwatch.CloudWatchMetric`
            instances.

        Side Effects:
            Performs paginated ``ListMetrics`` API calls.

        """
        from botocraft.services.cloudwatch import CloudWatchMetric

        request_args: dict[str, Any] = {
            "Namespace": self.serialize(Namespace),  # type: ignore[attr-defined]
            "MetricName": self.serialize(MetricName),  # type: ignore[attr-defined]
            "Dimensions": self.serialize(Dimensions),  # type: ignore[attr-defined]
        }
        matches: list[CloudWatchMetric] = []
        paginator = self.client.get_paginator("list_metrics")  # type: ignore[attr-defined]
        for response in paginator.paginate(
            **{key: value for key, value in request_args.items() if value is not None}
        ):
            for payload in response.get("Metrics", []):
                if not _metrics_match(
                    payload,
                    namespace=Namespace,
                    metric_name=MetricName,
                    dimensions=Dimensions,
                ):
                    continue
                matches.append(CloudWatchMetric(**payload))
        return matches
