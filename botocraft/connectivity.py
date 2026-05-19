"""Shared tunnel-aware connectivity helpers for private AWS resources."""

from __future__ import annotations

import socket
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, Callable, Self

from botocraft.config import BotocraftSettings

if TYPE_CHECKING:
    import boto3

    from botocraft.services.ec2 import Instance


#: Loopback host returned when a local SSM tunnel is active.
LOCALHOST = "127.0.0.1"
#: IMDS IPv4 endpoint used to detect whether the caller is running in AWS.
IMDS_HOST = "169.254.169.254"
#: IMDS HTTP port used for inside-AWS detection.
IMDS_PORT = 80
#: Socket timeout used for the IMDS reachability probe.
IMDS_TIMEOUT_SECONDS = 1.0


class ConnectionResolutionError(RuntimeError):
    """Raised when botocraft cannot resolve a usable connection target."""


class TunnelConfigurationError(ConnectionResolutionError):
    """Raised when local tunnel support is misconfigured or unavailable."""


class ResolvedConnectionTarget(AbstractContextManager["ResolvedConnectionTarget"]):
    """
    Represent one direct or tunneled connection target.

    Args:
        host: Reachable hostname before any tunnel is entered.
        port: Reachable port before any tunnel is entered.

    Keyword Args:
        tunneled: Whether this target should open a local tunnel on entry.
        tunnel_host_instance: EC2 instance used as the tunnel hop when tunneling.
        tunnel_context: Context manager that opens the underlying tunnel and yields
            the chosen local port.

    """

    #: Host callers should use once the target context is active.
    host: str
    #: Port callers should use once the target context is active.
    port: int
    #: Whether this target relies on a local tunnel.
    tunneled: bool
    #: Tunnel host instance used to establish the tunnel, when applicable.
    tunnel_host_instance: Instance | Any | None
    #: Underlying context manager that opens and closes the tunnel.
    _tunnel_context: AbstractContextManager[int] | None

    def __init__(
        self,
        host: str,
        port: int,
        *,
        tunneled: bool = False,
        tunnel_host_instance: Instance | Any | None = None,
        tunnel_context: AbstractContextManager[int] | None = None,
    ) -> None:
        """
        Initialize one resolved connection target.

        Args:
            host: Reachable hostname before any tunnel is entered.
            port: Reachable port before any tunnel is entered.

        Keyword Args:
            tunneled: Whether this target should open a local tunnel on entry.
            tunnel_host_instance: EC2 instance used as the tunnel hop when
                tunneling.
            tunnel_context: Context manager that opens the underlying tunnel and
                yields the chosen local port.

        """
        #: Host callers should use once the target context is active.
        self.host = host
        #: Port callers should use once the target context is active.
        self.port = port
        #: Whether this target relies on a local tunnel.
        self.tunneled = tunneled
        #: Tunnel host instance used to establish the tunnel, when applicable.
        self.tunnel_host_instance = tunnel_host_instance
        #: Underlying context manager that opens and closes the tunnel.
        self._tunnel_context = tunnel_context

    def __enter__(self) -> Self:
        """
        Enter the resolved target context and open the tunnel when needed.

        Side Effects:
            Opens a local SSM tunnel when this target is tunnel-backed.

        Returns:
            Active connection target with final host and port values.

        """
        if self._tunnel_context is not None:
            self.port = self._tunnel_context.__enter__()
            self.host = LOCALHOST
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Exit the resolved target context and close the tunnel when needed.

        Side Effects:
            Closes the underlying local SSM tunnel when one is active.

        Args:
            exc_type: Exception type raised inside the context, if any.
            exc_value: Exception value raised inside the context, if any.
            traceback: Exception traceback raised inside the context, if any.

        """
        if self._tunnel_context is not None:
            self._tunnel_context.__exit__(exc_type, exc_value, traceback)


class TunnelCapabilityValidator:
    """
    Verify that a tunnel host instance supports tunnel creation.

    This validator keeps resolver errors focused and user-facing, without leaking
    lower-level attribute errors from the tunnel host object.
    """

    def ensure_supported(self, tunnel_host_instance: Instance | Any) -> None:
        """
        Ensure the tunnel host instance exposes the expected tunnel API.

        Args:
            tunnel_host_instance: Candidate tunnel host instance.

        Raises:
            TunnelConfigurationError: The instance does not expose a callable
                ``tunnel`` method.

        """
        tunnel_method = getattr(tunnel_host_instance, "tunnel", None)
        if callable(tunnel_method):
            return
        msg = "Resolved tunnel host instance does not support SSM tunnel creation."
        raise TunnelConfigurationError(msg)


class TunnelHostLocator:
    """
    Find the tunnel host instance used for tunnel-backed connections.

    Args:
        settings: Runtime settings that define tunnel host tag filters.

    Keyword Args:
        session: Default boto3 session used for EC2 lookups.

    """

    #: Runtime settings that define tunnel host discovery filters.
    settings: BotocraftSettings
    #: Default boto3 session used for EC2 lookups.
    session: boto3.Session | None

    def __init__(
        self,
        *,
        settings: BotocraftSettings | None = None,
        session: boto3.Session | None = None,
    ) -> None:
        """
        Initialize the tunnel host locator.

        Keyword Args:
            settings: Runtime settings that define tunnel host tag filters.
            session: Default boto3 session used for EC2 lookups.

        """
        #: Runtime settings that define tunnel host discovery filters.
        self.settings = settings or BotocraftSettings()
        #: Default boto3 session used for EC2 lookups.
        self.session = session

    def find_instance(
        self,
        vpc_id: str,
        *,
        session: boto3.Session | None = None,
    ) -> Instance | Any | None:
        """
        Return the first running tunnel host instance in one VPC.

        Args:
            vpc_id: Target VPC identifier.

        Keyword Args:
            session: Explicit boto3 session override for this lookup.

        Returns:
            Matching EC2 instance, or ``None`` when no candidate is found.

        """
        from botocraft.services.common import Filter
        from botocraft.services.ec2 import Instance

        lookup_session = session or self.session
        filters = [
            Filter(
                Name=f"tag:{self.settings.tunnel.tunnel_host_tag_key}",
                Values=[self.settings.tunnel.tunnel_host_tag_value],
            ),
            Filter(Name="vpc-id", Values=[vpc_id]),
            Filter(Name="instance-state-name", Values=["running"]),
        ]
        manager = (
            Instance.objects.using(lookup_session)
            if lookup_session is not None
            else Instance.objects
        )
        instances = manager.list(Filters=filters)
        if instances:
            return instances[0]
        return None


class TunnelAwareConnectionResolver:
    """
    Resolve direct or tunneled connection targets for private resources.

    Args:
        settings: Runtime settings that control whether tunneling is enabled.

    Keyword Args:
        tunnel_host_locator: Custom tunnel host locator for tests or alternate
            lookup behavior.
        inside_aws_detector: Callable that reports whether the current process is
            running inside AWS.
        capability_validator: Validator used before building a tunnel-backed
            target.

    """

    #: Runtime settings that control whether tunneling is enabled.
    settings: BotocraftSettings
    #: Locator used to find tunnel host instances in a target VPC.
    tunnel_host_locator: TunnelHostLocator
    #: Callable that reports whether the current process is running inside AWS.
    inside_aws_detector: Callable[[], bool]
    #: Validator used before building a tunnel-backed target.
    capability_validator: TunnelCapabilityValidator

    def __init__(
        self,
        *,
        settings: BotocraftSettings | None = None,
        tunnel_host_locator: TunnelHostLocator | Any | None = None,
        inside_aws_detector: Callable[[], bool] | None = None,
        capability_validator: TunnelCapabilityValidator | None = None,
    ) -> None:
        """
        Initialize the connection resolver.

        Keyword Args:
            settings: Runtime settings that control whether tunneling is enabled.
            tunnel_host_locator: Custom tunnel host locator for tests or alternate
                lookup behavior.
            inside_aws_detector: Callable that reports whether the current process
                is running inside AWS.
            capability_validator: Validator used before building a tunnel-backed
                target.

        """
        #: Runtime settings that control whether tunneling is enabled.
        self.settings = settings or BotocraftSettings()
        #: Locator used to find tunnel host instances in a target VPC.
        self.tunnel_host_locator = tunnel_host_locator or TunnelHostLocator(
            settings=self.settings
        )
        #: Callable that reports whether the current process is running inside AWS.
        self.inside_aws_detector = inside_aws_detector or is_inside_aws
        #: Validator used before building a tunnel-backed target.
        self.capability_validator = capability_validator or TunnelCapabilityValidator()

    def open_connection_target(  # noqa: PLR0913
        self,
        *,
        host: str,
        port: int,
        vpc_id: str,
        session: boto3.Session | None = None,
        profile: str | None = None,
        resource_label: str | None = None,
    ) -> ResolvedConnectionTarget:
        """
        Resolve the connection target for one resource endpoint.

        Args:
            host: Resource endpoint hostname.
            port: Resource endpoint port.
            vpc_id: VPC that contains the target endpoint.

        Keyword Args:
            session: Explicit boto3 session override for tunnel host lookup.
            profile: AWS profile forwarded to the tunnel host tunnel helper.
            resource_label: Human-friendly resource description used in error
                messages.

        Raises:
            ConnectionResolutionError: No tunnel host instance can be found when a
                tunnel is required.
            TunnelConfigurationError: The resolved tunnel host instance cannot open
                tunnels.

        Returns:
            Context-managed connection target.

        """
        if not self.settings.tunnel.enabled or self.inside_aws_detector():
            return ResolvedConnectionTarget(host=host, port=port)

        tunnel_host = self.tunnel_host_locator.find_instance(vpc_id, session=session)
        if tunnel_host is None:
            label = resource_label or f"{host}:{port}"
            msg = (
                f"Unable to connect to {label}: no running tunnel host instance "
                f"matched tag {self.settings.tunnel.tunnel_host_tag_key}="
                f"{self.settings.tunnel.tunnel_host_tag_value!r} in VPC '{vpc_id}'."
            )
            raise ConnectionResolutionError(msg)

        self.capability_validator.ensure_supported(tunnel_host)
        tunnel_context = tunnel_host.tunnel(
            host=host,
            remote_port=port,
            profile=profile,
            ready_timeout_seconds=self.settings.tunnel.ready_timeout_seconds,
        )
        return ResolvedConnectionTarget(
            host=host,
            port=port,
            tunneled=True,
            tunnel_host_instance=tunnel_host,
            tunnel_context=tunnel_context,
        )


def is_inside_aws() -> bool:
    """
    Return whether the current process appears to be running inside AWS.

    This uses the same IMDS TCP reachability probe that `awsutils` uses for its
    first-pass tunnel gating logic.

    Returns:
        ``True`` when the IMDS endpoint is reachable, otherwise ``False``.

    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(IMDS_TIMEOUT_SECONDS)
        return sock.connect_ex((IMDS_HOST, IMDS_PORT)) == 0
