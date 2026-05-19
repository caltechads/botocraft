"""Tests for EC2 SSM tunnel hardening."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from botocraft.services.ec2 import Instance


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
            patch.object(
                Instance,
                "_InstanceModelMixin__maybe_resolve_ip",
                return_value="db.example",
            ),
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
