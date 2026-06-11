"""Tests for EC2 SSM tunnel hardening."""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

import pytest

from botocraft.config import BotocraftSettings, TunnelSettings
from botocraft.connectivity import LOCALHOST
from botocraft.services.ec2 import Instance

LDAP_HOST = "ldap.corp.internal"
LDAP_PORT = 389
LDAP_LOCAL_PORT = 10389
LDAP_TUNNEL_PORT = 15432
CUSTOM_TIMEOUT_SECONDS = 42
PRIVATE_IP = "10.0.0.15"
LDAPS_PORT = 636
LDAPS_LOCAL_PORT = 10636


def _ssm_parameters(command: list[str]) -> str:
    """Return the SSM ``--parameters`` value from one captured command."""
    index = command.index("--parameters") + 1
    return command[index]


class TestInstanceModelMixinTunnel:
    """Verify EC2 tunnel preflight and error reporting."""

    def test_open_tunnel_raises_when_aws_cli_missing(self) -> None:
        """Raise a clear error before attempting tunnel startup."""
        instance = Instance.model_construct(InstanceId="i-123", Tunnels=None)

        with (
            patch("botocraft.mixins.ec2.shutil.which", return_value=None),
            pytest.raises(RuntimeError, match="AWS CLI is not installed"),
        ):
            instance.open_tunnel(
                host="db.example",
                remote_port=3306,
                local_port=13306,
            )

    def test_open_tunnel_raises_when_start_session_unavailable(self) -> None:
        """Raise a clear error when the CLI lacks `ssm start-session`."""
        instance = Instance.model_construct(InstanceId="i-123", Tunnels=None)
        help_result = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))

        with (
            patch("botocraft.mixins.ec2.shutil.which", return_value="/usr/bin/aws"),
            patch("botocraft.mixins.ec2.subprocess.run", help_result),
            pytest.raises(
                RuntimeError,
                match="does not support `aws ssm start-session`",
            ),
        ):
            instance.open_tunnel(
                host="db.example",
                remote_port=3306,
                local_port=13306,
            )

    def test_open_tunnel_surfaces_early_process_stderr(self) -> None:
        """Include subprocess stderr when the tunnel dies during startup."""
        instance = Instance.model_construct(InstanceId="i-123", Tunnels=None)
        process = Mock()
        process.poll.side_effect = [1]
        process.communicate.return_value = (b"", b"expired SSO session")
        help_result = Mock(
            return_value=Mock(returncode=0, stdout="start-session", stderr="")
        )

        with (
            patch("botocraft.mixins.ec2.shutil.which", return_value="/usr/bin/aws"),
            patch("botocraft.mixins.ec2.subprocess.run", help_result),
            patch("botocraft.mixins.ec2.subprocess.Popen", return_value=process),
            patch("botocraft.mixins.ec2.time.sleep"),
            patch("botocraft.mixins.ec2.socket.socket") as socket_cls,
        ):
            socket_ctx = socket_cls.return_value.__enter__.return_value
            socket_ctx.connect_ex.return_value = 1
            with pytest.raises(RuntimeError, match="expired SSO session"):
                instance.open_tunnel(
                    host="db.example",
                    remote_port=3306,
                    local_port=13306,
                )

    def test_open_tunnel_passes_hostname_to_ssm_without_local_resolution(self) -> None:
        """Forward hostnames to SSM instead of resolving them locally."""
        instance = Instance.model_construct(InstanceId="i-123", Tunnels=None)
        process = Mock()
        process.poll.return_value = None
        help_result = Mock(
            return_value=Mock(returncode=0, stdout="start-session", stderr="")
        )
        popen_args: dict[str, Any] = {}

        def capture_popen(command: list[str], **_kwargs: Any) -> Mock:
            popen_args["command"] = command
            return process

        with (
            patch("botocraft.mixins.ec2.shutil.which", return_value="/usr/bin/aws"),
            patch("botocraft.mixins.ec2.subprocess.run", help_result),
            patch("botocraft.mixins.ec2.subprocess.Popen", side_effect=capture_popen),
            patch("botocraft.mixins.ec2.time.sleep"),
            patch("botocraft.mixins.ec2.socket.gethostbyname") as gethostbyname,
            patch("botocraft.mixins.ec2.socket.socket") as socket_cls,
        ):
            socket_ctx = socket_cls.return_value.__enter__.return_value
            socket_ctx.connect_ex.side_effect = [1, 0]
            local_port = instance.open_tunnel(
                host=LDAP_HOST,
                remote_port=LDAP_PORT,
                local_port=LDAP_LOCAL_PORT,
            )

        assert local_port == LDAP_LOCAL_PORT
        gethostbyname.assert_not_called()
        parameters = _ssm_parameters(popen_args["command"])
        expected = (
            f"host={LDAP_HOST},portNumber={LDAP_PORT},localPortNumber={LDAP_LOCAL_PORT}"
        )
        assert parameters == expected
        assert instance.Tunnels is not None
        assert LDAP_HOST in instance.Tunnels

    def test_open_tunnel_passes_literal_ip_to_ssm(self) -> None:
        """Keep literal IP addresses unchanged in SSM parameters."""
        instance = Instance.model_construct(InstanceId="i-123", Tunnels=None)
        process = Mock()
        process.poll.return_value = None
        help_result = Mock(
            return_value=Mock(returncode=0, stdout="start-session", stderr="")
        )
        popen_args: dict[str, Any] = {}

        def capture_popen(command: list[str], **_kwargs: Any) -> Mock:
            popen_args["command"] = command
            return process

        with (
            patch("botocraft.mixins.ec2.shutil.which", return_value="/usr/bin/aws"),
            patch("botocraft.mixins.ec2.subprocess.run", help_result),
            patch("botocraft.mixins.ec2.subprocess.Popen", side_effect=capture_popen),
            patch("botocraft.mixins.ec2.time.sleep"),
            patch("botocraft.mixins.ec2.socket.socket") as socket_cls,
        ):
            socket_ctx = socket_cls.return_value.__enter__.return_value
            socket_ctx.connect_ex.side_effect = [1, 0]
            instance.open_tunnel(
                host=PRIVATE_IP,
                remote_port=LDAPS_PORT,
                local_port=LDAPS_LOCAL_PORT,
            )

        parameters = _ssm_parameters(popen_args["command"])
        expected = (
            f"host={PRIVATE_IP},portNumber={LDAPS_PORT},localPortNumber={LDAPS_LOCAL_PORT}"
        )
        assert parameters == expected

    def test_open_connection_target_enters_tunnel_and_returns_localhost(self) -> None:
        """Return localhost and the forwarded port from open_connection_target()."""

        @contextmanager
        def fake_tunnel(
            host: str,
            remote_port: int,
            profile: str | None = None,
            local_port: int | None = None,
            ready_timeout_seconds: int = 10,
        ):
            assert host == LDAP_HOST
            assert remote_port == LDAP_PORT
            assert profile == "dev"
            assert local_port is None
            assert ready_timeout_seconds == CUSTOM_TIMEOUT_SECONDS
            yield LDAP_TUNNEL_PORT

        instance = Instance.model_construct(
            InstanceId="i-123",
            Tunnels=None,
            session=SimpleNamespace(profile_name="dev"),
        )

        with (
            patch.object(Instance, "tunnel", side_effect=fake_tunnel),
            patch(
                "botocraft.config.BotocraftSettings",
                return_value=BotocraftSettings(
                    tunnel=TunnelSettings(ready_timeout_seconds=CUSTOM_TIMEOUT_SECONDS)
                ),
            ) as settings_cls,
        ):
            target = instance.open_connection_target(
                host=LDAP_HOST,
                port=LDAP_PORT,
            )
            with target as active:
                assert active.host == LOCALHOST
                assert active.port == LDAP_TUNNEL_PORT
                assert active.tunneled is True
                assert active.tunnel_host_instance is instance

        settings_cls.assert_called_once()
