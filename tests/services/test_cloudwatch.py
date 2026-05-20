from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.cloudwatch import (
    AlarmMuteRule,
    AlarmMuteRuleManager,
    CloudWatchAnomalyDetector,
    CloudWatchAnomalyDetectorManager,
    CloudWatchDashboard,
    CloudWatchDashboardManager,
    CloudWatchInsightRule,
    CloudWatchInsightRuleManager,
    CloudWatchMetric,
    CloudWatchMetricManager,
    CloudWatchMetricStream,
    CloudWatchMetricStreamFilter,
    CloudWatchMetricStreamManager,
    CompositeAlarm,
    CompositeAlarmManager,
    MetricAlarm,
    MetricAlarmManager,
    MetricStreamStatisticsMetric,
    OTelEnrichmentStatus,
    OTelEnrichmentStatusManager,
)


def _metric_alarm_payload(name: str) -> dict[str, object]:
    return {
        "AlarmName": name,
        "AlarmArn": f"arn:aws:cloudwatch:us-west-2:123456789012:alarm:{name}",
        "StateValue": "OK",
    }


def _composite_alarm_payload(name: str) -> dict[str, object]:
    return {
        "AlarmName": name,
        "AlarmArn": f"arn:aws:cloudwatch:us-west-2:123456789012:alarm:{name}",
        "AlarmRule": f"ALARM({name}-child)",
        "StateValue": "OK",
    }


def _insight_rule_payload(
    name: str,
    *,
    managed_rule: bool = False,
) -> dict[str, object]:
    return {
        "Name": name,
        "State": "ENABLED",
        "Schema": '{"Name":"CloudWatchLogRule","Version":1}',
        "Definition": '{"AggregateOn":"Count"}',
        "ManagedRule": managed_rule,
    }


def _metric_payload(
    *,
    namespace: str = "Custom/App",
    metric_name: str = "RequestCount",
    dimensions: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return {
        "Namespace": namespace,
        "MetricName": metric_name,
        "Dimensions": dimensions or [{"Name": "Environment", "Value": "prod"}],
    }


def _alarm_mute_rule_summary(name: str) -> dict[str, object]:
    return {
        "AlarmMuteRuleArn": (
            f"arn:aws:cloudwatch:us-west-2:123456789012:alarm-mute-rule:{name}"
        ),
        "Status": "ACTIVE",
        "MuteType": "ONE_TIME",
    }


def _alarm_mute_rule_payload(name: str) -> dict[str, object]:
    return {
        "Name": name,
        **_alarm_mute_rule_summary(name),
        "Description": "mute overnight",
        "Rule": {
            "Schedule": {
                "Expression": "rate(1 day)",
                "Duration": "3600",
                "Timezone": "UTC",
            }
        },
        "MuteTargets": {"AlarmNames": ["cpu-high"]},
    }


def _anomaly_detector_payload(
    *,
    namespace: str = "AWS/EC2",
    metric_name: str = "CPUUtilization",
    dimensions: list[dict[str, str]] | None = None,
    stat: str = "Average",
) -> dict[str, object]:
    return {
        "Namespace": namespace,
        "MetricName": metric_name,
        "Dimensions": dimensions or [{"Name": "InstanceId", "Value": "i-1234567890"}],
        "Stat": stat,
        "StateValue": "TRAINED",
    }


class TestMetricAlarmManager:
    @patch("boto3.client")
    def test_get_filters_metric_alarms(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.describe_alarms.return_value = {
            "MetricAlarms": [_metric_alarm_payload("cpu-high")],
            "CompositeAlarms": [],
        }
        mock_boto3_client.return_value = mock_client

        manager = MetricAlarmManager()
        alarm = manager.get("cpu-high")

        mock_client.describe_alarms.assert_called_once_with(
            AlarmNames=["cpu-high"],
            AlarmTypes=["MetricAlarm"],
        )
        assert isinstance(alarm, MetricAlarm)
        assert alarm.AlarmName == "cpu-high"

    @patch("boto3.client")
    def test_list_filters_metric_alarms(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"MetricAlarms": [_metric_alarm_payload("cpu-high")]},
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = MetricAlarmManager()
        alarms = manager.list()

        mock_client.get_paginator.assert_called_once_with("describe_alarms")
        mock_paginator.paginate.assert_called_once_with(AlarmTypes=["MetricAlarm"])
        assert isinstance(alarms, PrimaryBoto3ModelQuerySet)
        assert len(alarms) == 1
        metric_alarm = cast("MetricAlarm", alarms[0])
        assert metric_alarm.AlarmName == "cpu-high"

    @patch("boto3.client")
    def test_enable_actions(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = MetricAlarmManager()
        manager.enable_actions("cpu-high")

        mock_client.enable_alarm_actions.assert_called_once_with(
            AlarmNames=["cpu-high"],
        )

    @patch("boto3.client")
    def test_set_state(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = MetricAlarmManager()
        manager.set_state("cpu-high", "ALARM", "testing")

        mock_client.set_alarm_state.assert_called_once_with(
            AlarmName="cpu-high",
            StateValue="ALARM",
            StateReason="testing",
        )

    @patch("boto3.client")
    def test_describe_history_filters_metric_alarms(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "AlarmHistoryItems": [
                    {
                        "AlarmName": "cpu-high",
                        "Timestamp": "2026-05-20T12:00:00Z",
                        "HistoryItemType": "StateUpdate",
                        "HistorySummary": "ok",
                    }
                ],
            },
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = MetricAlarmManager()
        history = manager.describe_history("cpu-high")

        mock_client.get_paginator.assert_called_once_with("describe_alarm_history")
        mock_paginator.paginate.assert_called_once_with(
            AlarmName="cpu-high",
            AlarmTypes=["MetricAlarm"],
        )
        assert len(history) == 1
        assert history[0].AlarmName == "cpu-high"


class TestMetricAlarmInstanceMethods:
    @patch.object(MetricAlarmManager, "set_state")
    def test_set_state_delegates_to_manager_with_alarm_name(
        self,
        mock_set_state: MagicMock,
    ) -> None:
        alarm = MetricAlarm(**_metric_alarm_payload("cpu-high"))

        alarm.set_state("ALARM", "testing", StateReasonData='{"version":"1.0"}')

        mock_set_state.assert_called_once_with(
            "cpu-high",
            "ALARM",
            "testing",
            StateReasonData='{"version":"1.0"}',
        )


class TestCompositeAlarmManager:
    @patch("boto3.client")
    def test_get_filters_composite_alarms(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.describe_alarms.return_value = {
            "MetricAlarms": [],
            "CompositeAlarms": [_composite_alarm_payload("ops-composite")],
        }
        mock_boto3_client.return_value = mock_client

        manager = CompositeAlarmManager()
        alarm = manager.get("ops-composite")

        mock_client.describe_alarms.assert_called_once_with(
            AlarmNames=["ops-composite"],
            AlarmTypes=["CompositeAlarm"],
        )
        assert isinstance(alarm, CompositeAlarm)
        assert alarm.AlarmName == "ops-composite"

    @patch("boto3.client")
    def test_disable_actions(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = CompositeAlarmManager()
        manager.disable_actions("ops-composite")

        mock_client.disable_alarm_actions.assert_called_once_with(
            AlarmNames=["ops-composite"],
        )

    @patch("boto3.client")
    def test_describe_history_filters_composite_alarms(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"AlarmHistoryItems": []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = CompositeAlarmManager()
        manager.describe_history("ops-composite")

        mock_paginator.paginate.assert_called_once_with(
            AlarmName="ops-composite",
            AlarmTypes=["CompositeAlarm"],
        )


class TestCloudWatchMetricStreamManager:
    @patch("boto3.client")
    def test_get_metric_stream(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_metric_stream.return_value = {
            "Arn": "arn:aws:cloudwatch:us-west-2:123456789012:metric-stream/primary",
            "Name": "primary",
            "State": "running",
            "FirehoseArn": "arn:aws:firehose:us-west-2:123456789012:deliverystream/primary",
            "RoleArn": "arn:aws:iam::123456789012:role/MetricStreamRole",
        }
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricStreamManager()
        stream = manager.get("primary")

        mock_client.get_metric_stream.assert_called_once_with(Name="primary")
        assert isinstance(stream, CloudWatchMetricStream)
        assert stream.Name == "primary"

    @patch("boto3.client")
    def test_list_metric_streams(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.list_metric_streams.return_value = {
            "Entries": [
                {
                    "Arn": "arn:aws:cloudwatch:us-west-2:123456789012:metric-stream/primary",
                    "Name": "primary",
                    "State": "running",
                }
            ],
        }
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricStreamManager()
        streams = manager.list()

        mock_client.list_metric_streams.assert_called_once_with()
        assert isinstance(streams, PrimaryBoto3ModelQuerySet)
        assert len(streams) == 1
        stream = cast("CloudWatchMetricStream", streams[0])
        assert stream.Name == "primary"

    @patch("boto3.client")
    def test_start_metric_stream(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricStreamManager()
        manager.start("primary")

        mock_client.start_metric_streams.assert_called_once_with(Names=["primary"])

    @patch("boto3.client")
    def test_stop_metric_stream(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricStreamManager()
        manager.stop("primary")

        mock_client.stop_metric_streams.assert_called_once_with(Names=["primary"])


class TestCloudWatchDashboardManager:
    @patch("boto3.client")
    def test_get_dashboard(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_dashboard.return_value = {
            "DashboardName": "ops",
            "DashboardArn": "arn:aws:cloudwatch::123456789012:dashboard/ops",
            "DashboardBody": '{"widgets":[]}',
        }
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchDashboardManager()
        dashboard = manager.get("ops")

        mock_client.get_dashboard.assert_called_once_with(DashboardName="ops")
        assert isinstance(dashboard, CloudWatchDashboard)
        assert dashboard.DashboardName == "ops"
        assert dashboard.DashboardBody == '{"widgets":[]}'

    @patch("boto3.client")
    def test_list_dashboards(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "DashboardEntries": [
                    {
                        "DashboardName": "ops",
                        "DashboardArn": "arn:aws:cloudwatch::123456789012:dashboard/ops",
                        "Size": 128,
                    }
                ],
            },
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchDashboardManager()
        dashboards = manager.list()

        mock_client.get_paginator.assert_called_once_with("list_dashboards")
        assert isinstance(dashboards, PrimaryBoto3ModelQuerySet)
        assert len(dashboards) == 1
        dashboard = cast("CloudWatchDashboard", dashboards[0])
        assert dashboard.DashboardName == "ops"


class TestCloudWatchInsightRuleManager:
    @patch("boto3.client")
    def test_list_filters_customer_managed_rules(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "InsightRules": [
                    _insight_rule_payload("customer-rule"),
                    _insight_rule_payload("managed-rule", managed_rule=True),
                ]
            },
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchInsightRuleManager()
        rules = manager.list()

        mock_client.get_paginator.assert_called_once_with("describe_insight_rules")
        mock_paginator.paginate.assert_called_once_with()
        assert isinstance(rules, PrimaryBoto3ModelQuerySet)
        assert len(rules) == 1
        rule = cast("CloudWatchInsightRule", rules[0])
        assert rule.Name == "customer-rule"

    @patch("boto3.client")
    def test_create_maps_name_to_rule_name(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchInsightRuleManager()
        manager.create(
            CloudWatchInsightRule(
                Name="customer-rule",
                State="ENABLED",
                Schema='{"Name":"CloudWatchLogRule","Version":1}',
                Definition='{"AggregateOn":"Count"}',
            )
        )

        mock_client.put_insight_rule.assert_called_once_with(
            RuleName="customer-rule",
            RuleState="ENABLED",
            RuleDefinition='{"AggregateOn":"Count"}',
        )

    @patch("boto3.client")
    def test_delete_uses_rule_names(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchInsightRuleManager()
        manager.delete("customer-rule")

        mock_client.delete_insight_rules.assert_called_once_with(
            RuleNames=["customer-rule"],
        )

    @patch("boto3.client")
    def test_get_returns_matching_customer_managed_rule(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.describe_insight_rules.return_value = {
            "InsightRules": [
                _insight_rule_payload("managed-rule", managed_rule=True),
                _insight_rule_payload("customer-rule"),
            ],
        }
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchInsightRuleManager()
        rule = manager.get("customer-rule")

        mock_client.describe_insight_rules.assert_called_once_with()
        assert isinstance(rule, CloudWatchInsightRule)
        assert rule.Name == "customer-rule"


class TestCloudWatchMetricManager:
    @patch("boto3.client")
    def test_list_metrics(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"Metrics": [_metric_payload()]},
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricManager()
        metrics = manager.list(Namespace="Custom/App")

        mock_client.get_paginator.assert_called_once_with("list_metrics")
        mock_paginator.paginate.assert_called_once_with(Namespace="Custom/App")
        assert isinstance(metrics, PrimaryBoto3ModelQuerySet)
        assert len(metrics) == 1
        metric = cast("CloudWatchMetric", metrics[0])
        assert metric.MetricName == "RequestCount"

    @patch("boto3.client")
    def test_get_matches_metric_identity(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Metrics": [
                    _metric_payload(metric_name="OtherMetric"),
                    _metric_payload(),
                ]
            },
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricManager()
        metric = manager.get(
            Namespace="Custom/App",
            MetricName="RequestCount",
            Dimensions=[{"Name": "Environment", "Value": "prod"}],
        )

        assert isinstance(metric, CloudWatchMetric)
        assert metric.Namespace == "Custom/App"
        assert metric.MetricName == "RequestCount"

    @patch("boto3.client")
    def test_publish_calls_put_metric_data(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricManager()
        model = CloudWatchMetric(**_metric_payload())
        manager.publish(
            model,
            MetricData=[{"Value": 1.0, "Timestamp": datetime(2026, 5, 21, tzinfo=UTC)}],
        )

        mock_client.put_metric_data.assert_called_once_with(
            Namespace="Custom/App",
            MetricData=[
                {
                    "MetricName": "RequestCount",
                    "Dimensions": [{"Name": "Environment", "Value": "prod"}],
                    "Value": 1.0,
                    "Timestamp": datetime(2026, 5, 21, tzinfo=UTC),
                }
            ],
        )

    @patch("boto3.client")
    def test_get_statistics(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_metric_statistics.return_value = {
            "Datapoints": [{"Timestamp": datetime(2026, 5, 21, tzinfo=UTC), "Average": 1.0}],
            "Label": "RequestCount",
        }
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricManager()
        model = CloudWatchMetric(**_metric_payload())
        start = datetime(2026, 5, 20, tzinfo=UTC)
        end = datetime(2026, 5, 21, tzinfo=UTC)
        datapoints = manager.get_statistics(
            model,
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        mock_client.get_metric_statistics.assert_called_once_with(
            Namespace="Custom/App",
            MetricName="RequestCount",
            Dimensions=[{"Name": "Environment", "Value": "prod"}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )
        assert datapoints == [
            {"Timestamp": datetime(2026, 5, 21, tzinfo=UTC), "Average": 1.0}
        ]

    @patch("boto3.client")
    def test_get_data(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_metric_data.return_value = {
            "MetricDataResults": [{"Id": "m1", "Timestamps": [], "Values": []}],
        }
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricManager()
        model = CloudWatchMetric(**_metric_payload())
        start = datetime(2026, 5, 20, tzinfo=UTC)
        end = datetime(2026, 5, 21, tzinfo=UTC)
        results = manager.get_data(
            model,
            StartTime=start,
            EndTime=end,
            Period=60,
            Stat="Average",
        )

        mock_client.get_metric_data.assert_called_once()
        call_kwargs = mock_client.get_metric_data.call_args.kwargs
        assert call_kwargs["StartTime"] == start
        assert call_kwargs["EndTime"] == end
        assert len(call_kwargs["MetricDataQueries"]) == 1
        assert call_kwargs["MetricDataQueries"][0]["Id"] == "m1"
        assert results == [{"Id": "m1", "Timestamps": [], "Values": []}]

    @patch("boto3.client")
    def test_widget_image_returns_bytes(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_metric_widget_image.return_value = {
            "MetricWidgetImage": b"png-bytes",
        }
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchMetricManager()
        image = manager.widget_image(MetricWidget='{"metrics":[]}')

        mock_client.get_metric_widget_image.assert_called_once_with(
            MetricWidget='{"metrics":[]}'
        )
        assert image == b"png-bytes"


class TestAlarmMuteRuleManager:
    @patch("boto3.client")
    def test_get(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_alarm_mute_rule.return_value = _alarm_mute_rule_payload(
            "overnight-mute"
        )
        mock_boto3_client.return_value = mock_client

        manager = AlarmMuteRuleManager()
        rule = manager.get("overnight-mute")

        mock_client.get_alarm_mute_rule.assert_called_once_with(
            AlarmMuteRuleName="overnight-mute",
        )
        assert isinstance(rule, AlarmMuteRule)
        assert rule.Name == "overnight-mute"

    @patch("boto3.client")
    def test_list(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"AlarmMuteRuleSummaries": [_alarm_mute_rule_summary("overnight-mute")]},
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = AlarmMuteRuleManager()
        rules = manager.list(AlarmName="cpu-high", Statuses=["ACTIVE"])

        mock_client.get_paginator.assert_called_once_with("list_alarm_mute_rules")
        mock_paginator.paginate.assert_called_once_with(
            AlarmName="cpu-high",
            Statuses=["ACTIVE"],
        )
        assert isinstance(rules, PrimaryBoto3ModelQuerySet)
        assert len(rules) == 1
        mute_rule = cast("AlarmMuteRule", rules[0])
        assert mute_rule.Status == "ACTIVE"

    @patch("boto3.client")
    def test_create(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = AlarmMuteRuleManager()
        model = AlarmMuteRule(**_alarm_mute_rule_payload("overnight-mute"))
        manager.create(model)

        mock_client.put_alarm_mute_rule.assert_called_once()
        call_kwargs = mock_client.put_alarm_mute_rule.call_args.kwargs
        assert call_kwargs["Name"] == "overnight-mute"
        assert call_kwargs["MuteTargets"] == {"AlarmNames": ["cpu-high"]}

    @patch("boto3.client")
    def test_delete(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = AlarmMuteRuleManager()
        manager.delete("overnight-mute")

        mock_client.delete_alarm_mute_rule.assert_called_once_with(
            AlarmMuteRuleName="overnight-mute",
        )


class TestOTelEnrichmentStatusManager:
    @patch("boto3.client")
    def test_get(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_otel_enrichment.return_value = {"Status": "Running"}
        mock_boto3_client.return_value = mock_client

        manager = OTelEnrichmentStatusManager()
        status = manager.get()

        mock_client.get_otel_enrichment.assert_called_once_with()
        assert isinstance(status, OTelEnrichmentStatus)
        assert status.Status == "Running"
        assert status.pk == "otel-enrichment"

    @patch("boto3.client")
    def test_start(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = OTelEnrichmentStatusManager()
        manager.start()

        mock_client.start_otel_enrichment.assert_called_once_with()

    @patch("boto3.client")
    def test_stop(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = OTelEnrichmentStatusManager()
        manager.stop()

        mock_client.stop_otel_enrichment.assert_called_once_with()


class TestCloudWatchMetricInstanceMethods:
    @patch.object(CloudWatchMetricManager, "publish")
    def test_publish_delegates_to_manager_with_model(
        self,
        mock_publish: MagicMock,
    ) -> None:
        metric = CloudWatchMetric(**_metric_payload())
        metric_data = [{"Value": 1.0, "Timestamp": datetime(2026, 5, 21, tzinfo=UTC)}]

        metric.publish(MetricData=metric_data)

        mock_publish.assert_called_once_with(metric, metric_data)

    @patch.object(CloudWatchMetricManager, "get_data")
    def test_get_data_delegates_to_manager_with_model(
        self,
        mock_get_data: MagicMock,
    ) -> None:
        metric = CloudWatchMetric(**_metric_payload())
        start = datetime(2026, 5, 20, tzinfo=UTC)
        end = datetime(2026, 5, 21, tzinfo=UTC)
        mock_get_data.return_value = [{"Id": "m1", "Timestamps": [], "Values": []}]

        results = metric.get_data(
            StartTime=start,
            EndTime=end,
            Period=60,
            Stat="Average",
        )

        mock_get_data.assert_called_once_with(
            metric,
            start,
            end,
            60,
            "Average",
            Unit=None,
            ScanBy=None,
        )
        assert results == [{"Id": "m1", "Timestamps": [], "Values": []}]

    @patch.object(CloudWatchMetricManager, "get_statistics")
    def test_get_statistics_delegates_to_manager_with_model(
        self,
        mock_get_statistics: MagicMock,
    ) -> None:
        metric = CloudWatchMetric(**_metric_payload())
        start = datetime(2026, 5, 20, tzinfo=UTC)
        end = datetime(2026, 5, 21, tzinfo=UTC)
        mock_get_statistics.return_value = [
            {"Timestamp": datetime(2026, 5, 21, tzinfo=UTC), "Average": 1.0}
        ]

        datapoints = metric.get_statistics(
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        mock_get_statistics.assert_called_once_with(
            metric,
            start,
            end,
            60,
            Statistics=["Average"],
            ExtendedStatistics=None,
            Unit=None,
        )
        assert datapoints == [
            {"Timestamp": datetime(2026, 5, 21, tzinfo=UTC), "Average": 1.0}
        ]

    @patch.object(CloudWatchMetricManager, "widget_image")
    def test_widget_image_delegates_to_manager(
        self,
        mock_widget_image: MagicMock,
    ) -> None:
        mock_widget_image.return_value = b"png-bytes"

        image = CloudWatchMetric(**_metric_payload()).widget_image(
            MetricWidget='{"metrics":[]}'
        )

        mock_widget_image.assert_called_once_with('{"metrics":[]}')
        assert image == b"png-bytes"


class TestCloudWatchMetricModelHelpers:
    def test_to_stream_include_filter(self) -> None:
        metric = CloudWatchMetric(**_metric_payload())
        stream_filter = metric.to_stream_include_filter()

        assert isinstance(stream_filter, CloudWatchMetricStreamFilter)
        assert stream_filter.Namespace == "Custom/App"
        assert stream_filter.MetricNames == ["RequestCount"]

    def test_to_stream_statistics_metric(self) -> None:
        metric = CloudWatchMetric(**_metric_payload())
        statistics_metric = metric.to_stream_statistics_metric()

        assert isinstance(statistics_metric, MetricStreamStatisticsMetric)
        assert statistics_metric.Namespace == "Custom/App"
        assert statistics_metric.MetricName == "RequestCount"


class TestCloudWatchAnomalyDetectorManager:
    @patch("boto3.client")
    def test_list_calls_describe_anomaly_detectors(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"AnomalyDetectors": [_anomaly_detector_payload()]},
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchAnomalyDetectorManager()
        detectors = manager.list()

        mock_client.get_paginator.assert_called_once_with("describe_anomaly_detectors")
        mock_paginator.paginate.assert_called_once_with()
        assert isinstance(detectors, PrimaryBoto3ModelQuerySet)
        assert len(detectors) == 1
        detector = cast("CloudWatchAnomalyDetector", detectors[0])
        assert detector.MetricName == "CPUUtilization"

    @patch("boto3.client")
    def test_create_calls_put_anomaly_detector(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchAnomalyDetectorManager()
        model = CloudWatchAnomalyDetector(**_anomaly_detector_payload())
        manager.create(model)

        mock_client.put_anomaly_detector.assert_called_once_with(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": "i-1234567890"}],
            Stat="Average",
        )

    @patch("boto3.client")
    def test_delete_calls_delete_anomaly_detector(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchAnomalyDetectorManager()
        model = CloudWatchAnomalyDetector(**_anomaly_detector_payload())
        manager.delete(model)

        mock_client.delete_anomaly_detector.assert_called_once_with(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": "i-1234567890"}],
            Stat="Average",
        )

    @patch("boto3.client")
    def test_get_filters_with_provided_kwargs(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.describe_anomaly_detectors.return_value = {
            "AnomalyDetectors": [
                _anomaly_detector_payload(stat="Sum"),
                _anomaly_detector_payload(stat="Average"),
            ],
        }
        mock_boto3_client.return_value = mock_client

        manager = CloudWatchAnomalyDetectorManager()
        detector = manager.get(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": "i-1234567890"}],
            Stat="Average",
        )

        mock_client.describe_anomaly_detectors.assert_called_once_with(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": "i-1234567890"}],
        )
        assert isinstance(detector, CloudWatchAnomalyDetector)
        assert detector.Stat == "Average"
