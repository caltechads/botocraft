"""Tests for tunnel-aware connectivity helpers."""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest

from botocraft.config import BotocraftSettings, TunnelSettings
from botocraft.connectivity import (
    ConnectionResolutionError,
    TunnelAwareConnectionResolver,
    TunnelHostLocator,
)

DB_PORT = 3306
REDIS_PORT = 6379
DOCDB_PORT = 27017
CUSTOM_TIMEOUT_SECONDS = 42
LOCAL_TUNNEL_PORT = 15432


class TestTunnelHostLocator:
    """Verify tunnel host instance discovery behavior."""

    def test_uses_configured_tag_filters(self) -> None:
        """Look up tunnel hosts with configurable tag key/value filters."""
        session = cast("Any", object())
        expected_instance = SimpleNamespace(InstanceId="i-123")
        list_mock = Mock(return_value=[expected_instance])
        using_mock = Mock(return_value=SimpleNamespace(list=list_mock))

        settings = BotocraftSettings(
            tunnel=TunnelSettings(
                tunnel_host_tag_key="Role",
                tunnel_host_tag_value="jump-host",
            )
        )

        with patch("botocraft.services.ec2.Instance") as instance_cls:
            instance_cls.objects.using = using_mock
            locator = TunnelHostLocator(settings=settings, session=session)
            resolved = locator.find_instance("vpc-123")

        assert resolved is expected_instance
        using_mock.assert_called_once_with(session)
        filters = list_mock.call_args.kwargs["Filters"]
        assert [flt.Name for flt in filters] == [
            "tag:Role",
            "vpc-id",
            "instance-state-name",
        ]
        assert [flt.Values for flt in filters] == [
            ["jump-host"],
            ["vpc-123"],
            ["running"],
        ]


class TestTunnelAwareConnectionResolver:
    """Verify direct and tunneled endpoint resolution."""

    def test_returns_direct_target_inside_aws(self) -> None:
        """Keep the original endpoint when running inside AWS."""
        resolver = TunnelAwareConnectionResolver(
            settings=BotocraftSettings(),
            inside_aws_detector=lambda: True,
        )

        with resolver.open_connection_target(
            host="db.example",
            port=DB_PORT,
            vpc_id="vpc-123",
        ) as target:
            assert target.host == "db.example"
            assert target.port == DB_PORT
            assert target.tunneled is False
            assert target.tunnel_host_instance is None

    def test_returns_direct_target_when_tunnel_disabled(self) -> None:
        """Bypass tunnel host lookup when tunneling is disabled."""
        locator = Mock()
        resolver = TunnelAwareConnectionResolver(
            settings=BotocraftSettings(tunnel=TunnelSettings(enabled=False)),
            tunnel_host_locator=locator,
            inside_aws_detector=lambda: False,
        )

        with resolver.open_connection_target(
            host="cache.example",
            port=REDIS_PORT,
            vpc_id="vpc-123",
        ) as target:
            assert target.host == "cache.example"
            assert target.port == REDIS_PORT
            assert target.tunneled is False

        locator.find_instance.assert_not_called()

    def test_raises_when_no_tunnel_host_exists_outside_aws(self) -> None:
        """Raise a clear error only when the tunnel path needs a tunnel host."""
        locator = Mock()
        locator.find_instance.return_value = None
        resolver = TunnelAwareConnectionResolver(
            settings=BotocraftSettings(),
            tunnel_host_locator=locator,
            inside_aws_detector=lambda: False,
        )

        with pytest.raises(ConnectionResolutionError) as exc_info:
            resolver.open_connection_target(
                host="docdb.example",
                port=DOCDB_PORT,
                vpc_id="vpc-123",
                resource_label="DocumentDB cluster 'main'",
            )

        assert "Unable to connect" in str(exc_info.value)
        assert "DocumentDB cluster 'main'" in str(exc_info.value)

    def test_enters_tunnel_and_returns_localhost_target(self) -> None:
        """Return localhost and the forwarded port when a tunnel is needed."""

        @contextmanager
        def fake_tunnel(
            host: str,
            remote_port: int,
            profile: str | None = None,
            ready_timeout_seconds: int | None = None,
        ):
            assert host == "db.example"
            assert remote_port == DB_PORT
            assert profile == "dev"
            assert ready_timeout_seconds == CUSTOM_TIMEOUT_SECONDS
            yield LOCAL_TUNNEL_PORT

        tunnel_host = SimpleNamespace(
            InstanceId="i-123",
            tunnel=fake_tunnel,
        )
        locator = Mock()
        locator.find_instance.return_value = tunnel_host
        resolver = TunnelAwareConnectionResolver(
            settings=BotocraftSettings(
                tunnel=TunnelSettings(ready_timeout_seconds=CUSTOM_TIMEOUT_SECONDS)
            ),
            tunnel_host_locator=locator,
            inside_aws_detector=lambda: False,
        )

        with resolver.open_connection_target(
            host="db.example",
            port=DB_PORT,
            vpc_id="vpc-123",
            profile="dev",
        ) as target:
            assert target.host == "127.0.0.1"
            assert target.port == LOCAL_TUNNEL_PORT
            assert target.tunneled is True
            assert target.tunnel_host_instance is tunnel_host
