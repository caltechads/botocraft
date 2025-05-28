import socket
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from ipaddress import ip_address
from typing import TYPE_CHECKING, Callable, Dict, List, Literal, Optional, cast
from zoneinfo import ZoneInfo

import psutil

if TYPE_CHECKING:
    from botocraft.services import (
        AMI,
        Finding,
        Instance,
        Reservation,
        Tag,
        TagSpecification,
    )
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet


#: The EC2 resource types.  We need this for specifying the proper tag for
#: resources in EC2.
ResourceType = Literal[
    "capacity-reservation",
    "client-vpn-endpoint",
    "customer-gateway",
    "carrier-gateway",
    "coip-pool",
    "dedicated-host",
    "dhcp-options",
    "egress-only-internet-gateway",
    "elastic-ip",
    "elastic-gpu",
    "export-image-task",
    "export-instance-task",
    "fleet",
    "fpga-image",
    "host-reservation",
    "image",
    "import-image-task",
    "import-snapshot-task",
    "instance",
    "instance-event-window",
    "internet-gateway",
    "ipam",
    "ipam-pool",
    "ipam-scope",
    "ipv4pool-ec2",
    "ipv6pool-ec2",
    "key-pair",
    "launch-template",
    "local-gateway",
    "local-gateway-route-table",
    "local-gateway-virtual-interface",
    "local-gateway-virtual-interface-group",
    "local-gateway-route-table-vpc-association",
    "local-gateway-route-table-virtual-interface-group-association",
    "natgateway",
    "network-acl",
    "network-interface",
    "network-insights-analysis",
    "network-insights-path",
    "network-insights-access-scope",
    "network-insights-access-scope-analysis",
    "placement-group",
    "prefix-list",
    "replace-root-volume-task",
    "reserved-instances",
    "route-table",
    "security-group",
    "security-group-rule",
    "snapshot",
    "spot-fleet-request",
    "spot-instances-request",
    "subnet",
    "subnet-cidr-reservation",
    "traffic-mirror-filter",
    "traffic-mirror-session",
    "traffic-mirror-target",
    "transit-gateway",
    "transit-gateway-attachment",
    "transit-gateway-connect-peer",
    "transit-gateway-multicast-domain",
    "transit-gateway-policy-table",
    "transit-gateway-route-table",
    "transit-gateway-route-table-announcement",
    "volume",
    "vpc",
    "vpc-endpoint",
    "vpc-endpoint-connection",
    "vpc-endpoint-service",
    "vpc-endpoint-service-permission",
    "vpc-peering-connection",
    "vpn-connection",
    "vpn-gateway",
    "vpc-flow-log",
    "capacity-reservation-fleet",
    "traffic-mirror-filter-rule",
    "vpc-endpoint-connection-device-type",
    "verified-access-instance",
    "verified-access-group",
    "verified-access-endpoint",
    "verified-access-policy",
    "verified-access-trust-provider",
    "vpn-connection-device-type",
    "vpc-block-public-access-exclusion",
    "ipam-resource-discovery",
    "ipam-resource-discovery-association",
    "instance-connect-endpoint",
]

# ----------
# Decorators
# ----------


def ec2_instances_only(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps a boto3 method that returns a list of :py:class:`Reservation` objects
    to return a list of :py:class:`Instance` objects instead.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        qs = func(*args, **kwargs)
        instances: List["Instance"] = []  # noqa: UP037
        for reservation in qs.results:
            instances.extend(cast("List[Instance]", reservation.Instances))  # type: ignore[attr-defined]
        return PrimaryBoto3ModelQuerySet(instances)  # type: ignore[arg-type]

    return wrapper


def ec2_instance_only(
    func: Callable[..., Optional["Reservation"]],
) -> Callable[..., Optional["Instance"]]:
    """
    Wraps a boto3 method that returns a list of :py:class:`Reservation` objects
    to return a single :py:class:`Instance` object instead.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Optional["Instance"]:
        reservation = func(*args, **kwargs)
        if not reservation:
            return None
        return cast("List[Instance]", reservation.Instances)[0]

    return wrapper


# -------------
# Mixin classes
# -------------


class EC2TagsManagerMixin:
    """
    A mixin is used on on :py:class:`botocraft.services.ec2.InstanceManager`
    to convert the odd EC2 tag list to a :py:class:`TagSpecification` object.
    """

    def convert_tags(
        self, tags: List["Tag"] | None, resource_type: ResourceType
    ) -> Optional["TagSpecification"]:
        """
        Given a TagList, convert it to a TagSpecification with ResourceType of
        ``resource_type``.

        Args:
            tags: the list of :py:class:`Tag` objects to convert.
            resource_type: the EC2 resource type.

        Returns:
            A :py:class:`TagSpecification` object, or ``None`` if ``tags`` is
            ``None``.

        """
        from botocraft.services import TagSpecification

        if tags is None:
            return None
        return TagSpecification(ResourceType=resource_type, Tags=tags)


class InstanceModelMixin:
    """
    Used on :py:class:`botocraft.services.ec2.Instance` to add miscellaneous
    methods to the class that are not normally part of the object.
    """

    def __maybe_resolve_ip(self, host: str) -> str:
        """
        Given a hostname or IP address, return the IP address.  If the host is
        an IP address, return it as is.  If the host is a hostname, resolve it
        to an IP address.

        Args:
            host: either an IP address of the remote host to connect to, or
                a hostname of that host

        Returns:
            The IP address of the host.

        """
        try:
            ip_address(host)
        except ValueError:
            # If it is not an IP address, then it must be a hostname.
            # Resolve the hostname to an IP address.
            try:
                return socket.gethostbyname(host)
            except socket.gaierror as e:
                msg = f"Could not resolve hostname {host}: {e}"
                raise RuntimeError(msg) from e
        return host

    def __find_open_port(self, start_port: int) -> int:
        """
        Find an open port starting from ``start_port``.  This is used to find
        an open port for the SSH tunnel.

        Args:
            start_port: The port to start searching from.

        Returns:
            An open port.

        Raises:
            ValueError: If no open port is found.

        """
        port = start_port
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(("127.0.0.1", port)) != 0:
                    break
                port += 1
                if port > 65535:  # noqa: PLR2004
                    msg = f"No available port found starting at {start_port}."
                    raise ValueError(msg)
        return port

    @contextmanager
    def tunnel(
        self,
        host: str,
        remote_port: int,
        local_port: int | None = None,
        profile: str | None = None,
    ):
        """
        A context manager for opening and closing a tunnel.

        This will call `open_tunnel` when entering the context and
        `close_tunnel` when exiting the context.

        Args:
            host: The remote host to connect to (IP or hostname).
            remote_port: The remote port to connect to.
            local_port: The local port to use. If None, an unused port will be chosen.
            profile: The AWS profile to use. If None, the default profile will be used.

        Raises:
            ValueError: If the local port is already in use.
            RuntimeError: If the instance is not connected to SSM or if there
                is an error when starting the session or SSH tunnel.

        Yields:
            The local port used for the tunnel.

        """
        local_port = self.open_tunnel(
            host=host,
            remote_port=remote_port,
            local_port=local_port,
            profile=profile,
        )
        try:
            yield local_port
        finally:
            self.close_tunnel(host=host, local_port=local_port)

    def open_tunnel(
        self,
        host: str,
        remote_port: int,
        local_port: int | None = None,
        profile: str | None = None,
    ) -> int:
        """
        Open a tunnel to the instance using SSM and SSH. This is useful for
        connecting to a database or other service on the instance that
        is in a private subnet. This will open a tunnel from the ``local_port``
        on the local machine through the instance to the ``remote_port`` on
        ``host``.

        If ``local_port`` is not specified, a random port will be chosen
        starting from between 8800 and 65535.

        Args:
            host: either an IP address of the remote host to connect to, or
                a hostname of that host
            remote_port: The remote port to connect to.

        Keyword Args:
            local_port: The local port to connect to.
            profile: The AWS profile to use. If not specified, the default
                profile will be used.

        Raises:
            ValueError: If the local port is already in use.
            RuntimeError: If the instance is not connected to SSM or if there
                is an error when starting the session or SSH tunnel.

        Returns:
            The local port that was used for the tunnel.

        """
        # Find an unused local port if local_port is None
        if local_port is None:
            local_port = self.__find_open_port(8800)
        else:
            # Check if the local port is already in use
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(("127.0.0.1", local_port)) == 0:
                    msg = f"Local port {local_port} is already in use."
                    raise ValueError(msg)
        host_ip = self.__maybe_resolve_ip(host)

        # Build the AWS SSM start-session command
        ssm_command = [
            "aws",
            "ssm",
            "start-session",
            "--target",
            self.InstanceId,  # type: ignore[attr-defined]
            "--document-name",
            "AWS-StartPortForwardingSessionToRemoteHost",
            "--parameters",
            f"host={host_ip},portNumber={remote_port},localPortNumber={local_port}",
        ]

        if profile:
            ssm_command.extend(["--profile", profile])

        try:
            # Start the SSM session
            ssm_process = subprocess.Popen(
                ssm_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as e:
            msg = "AWS CLI is not installed or not in PATH"
            raise RuntimeError(msg) from e

        # Wait for the port to be open
        for _ in range(40):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(("127.0.0.1", local_port)) == 0:
                    break
            time.sleep(0.25)
        else:
            # If the port is not open after 10 seconds, kill the process
            ssm_process.kill()
            msg = (
                f"Failed to open tunnel to {host_ip}:{remote_port} on local "
                f"port {local_port}."
            )
            raise RuntimeError(msg)

        # Store the processes for later management
        if self.Tunnels is None:  # type: ignore[has-type]
            self.Tunnels = {}  # type: ignore[var-annotated]
        if host_ip not in self.Tunnels:
            self.Tunnels[host_ip] = []
        self.Tunnels[host_ip].append(
            {
                "ssm_process": ssm_process,
                "local_port": local_port,
            }
        )
        return local_port

    def close_tunnel(self, host: str, local_port: int | None = None) -> None:
        """
        Close one or more tunnels to ``host``. This will terminate the SSM
        session(s) and SSH process(es) that were opened by
        :py:meth:`start_tunnel`.

        If ``local_port`` is not specified, all tunnels to the host will be
        closed. If ``local_port`` is specified, only the tunnel to that port
        will be closed.

        Args:
            host: Either an IP address of the remote host to connect to, or
                a hostname of that host.

        Keyword Args:
            local_port: The local port to close. If not specified, all
                tunnels to the host will be closed.

        Raises:
            ValueError: If no tunnels are found for the given host or port.

        """

        def terminate_process(process: subprocess.Popen) -> None:
            """
            Helper function to terminate a process and its children.

            Args:
                process: The process to terminate.

            """
            try:
                for child in psutil.Process(process.pid).children(recursive=True):
                    child.terminate()
                process.terminate()
            except psutil.NoSuchProcess:
                pass

        host_ip = self.__maybe_resolve_ip(host)

        if self.Tunnels is None or host_ip not in self.Tunnels:
            msg = f"No open tunnels found for {host_ip}. Did you call start_tunnel?"
            raise ValueError(msg)

        tunnels = self.Tunnels[host_ip]

        if local_port is not None:
            # Close the specific tunnel for the given local port
            for tunnel in tunnels:
                if tunnel["local_port"] == local_port:
                    terminate_process(tunnel["ssm_process"])
                    tunnels.remove(tunnel)
                    break
            else:
                msg = f"No open tunnel found for {host_ip} on local port {local_port}."
                raise ValueError(msg)
        else:
            # Close all tunnels for the given host
            for tunnel in tunnels:
                terminate_process(tunnel["ssm_process"])
            del self.Tunnels[host_ip]


class SecurityGroupModelMixin:
    """
    A mixin is used on :py:class:`botocraft.services.ec2.SecurityGroup` to
    enhance the ``.save()`` method to allow for managing ingress and egress
    rules at the same time as saving the security group.

    Normally this is done with several boto3 calls, but this mixin allows for a
    single call to ``.save()`` to create a security group and manage the rules.
    """

    def save(self, **kwargs):
        """
        Save the model.  For security groups, ingress rules are managed via
        separate boto3 calls than the security group itself.  This override of
        the ``save`` method will allow the user to create a security group and
        add ingress rules in one step.
        """
        # TODO: this needs to be enhanced to handle egress rules as well.
        if not self.pk:
            group_id = self.objects.create(self, **kwargs)
            self.objects.using(self.session).authorize_ingress(
                group_id, self.IpPermissions, **kwargs
            )
        else:
            old_obj = self.objects.using(self.session).get(self.pk)
            if self.IpPermissions != old_obj.IpPermissions:
                if old_obj.IpPermissions:
                    self.objects.using(self.session).revoke_ingress(
                        self.pk, old_obj.IpPermissions, **kwargs
                    )
                if self.IpPermissions:
                    self.objects.using(self.session).authorize_ingress(
                        self.pk, self.IpPermissions, **kwargs
                    )


class AMIManagerMixin:
    def in_use(
        self,
        owners: List[str] | None = None,
        tags: Dict[str, str] | None = None,
        created_since: datetime | None = None,
    ) -> List["AMI"]:
        """
        Return a list of AMIs that are currently in use by a running or stopped
        instance.

        Keyword Args:
            owners: Scopes the results to images with the specified owners. You
                can specify a combination of Amazon Web Services account IDs,
                ``self``, ``amazon``, and ``aws-marketplace``. If you omit this
                parameter, the results include all images for which you have launch
                permissions, regardless of ownership.  If not specified, the
                default is ``self``.
            tags: Filters the AMIs to those who match the these tags.
            created_since: Filters the AMIs to those created since this date.

        """
        from botocraft.services import Filter, Instance

        _owners = owners if owners else ["self"]
        _filters: List[Filter] | None = None
        if tags:
            _filters = [
                Filter(Name=f"tag:{key}", Values=[value]) for key, value in tags.items()
            ]

        if created_since:
            # First convert the timezone to UTC if this is a timezone-aware
            # datetime object.
            if created_since.tzinfo:
                created_since = created_since.astimezone(ZoneInfo("UTC"))
            # Now append the filter to the list of filters for the AMI listing.
            if _filters is None:
                _filters = []
            _filters.append(
                Filter(Name="creation-date", Values=[created_since.isoformat()])
            )
        amis = self.list(Owners=_owners, Filters=_filters)  # type: ignore[attr-defined]
        _filters = [Filter(Name="image-id", Values=[ami.ImageId for ami in amis])]
        instances: List[Instance] = Instance.objects.list(Filters=_filters)
        in_use_amis: List["AMI"] = []  # noqa: UP037
        for instance in instances:
            for ami in amis:
                if instance.ImageId == ami.ImageId:
                    if ami not in in_use_amis:
                        in_use_amis.append(ami)
        return list(in_use_amis)


class AMIModelMixin:
    @property
    def in_use(self) -> bool:
        """
        Return ``True`` if the AMI is in use by a running or stopped instance.
        """
        from botocraft.services import Filter, Instance

        _filters = [Filter(Name="image-id", Values=[self.ImageId])]  # type: ignore[attr-defined]
        instances: List[Instance] = Instance.objects.all(Filters=_filters)
        return bool(instances)

    @property
    def vulnerabilities(self) -> "PrimaryBoto3ModelQuerySet":
        """
        Return a list of vulnerabilities for the instance.  This is a
        convenience method to get the vulnerabilities for the instance.

        Returns:
            A list of :py:class:`Finding` objects.

        """
        from botocraft.services import FilterCriteria, Finding, StringFilter

        return Finding.objects.using(self.session).list(  # type: ignore[attr-defined]
            FilterCriteria(
                ec2InstanceImageId=[
                    StringFilter(value=self.ImageId, comparison="EQUALS")  # type: ignore[attr-defined]
                ],
            ),
        )


class SubnetModelMixin:
    """
    A mixin is used on :py:class:`botocraft.services.ec2.Subnet` to add
    miscellaneous methods to the class that are not normally part of the
    object.
    """

    @property
    def vulnerabilities(self) -> List["Finding"]:
        """
        Return a list of vulnerabilities for the instance.  This is a
        convenience method to get the vulnerabilities for the instance.

        Returns:
            A list of :py:class:`Finding` objects.

        """
        from botocraft.services import FilterCriteria, Finding, StringFilter

        return Finding.objects.using(self.session).list(  # type: ignore[attr-defined]
            filterCriteria=FilterCriteria(
                ec2InstanceSubnetId=[
                    StringFilter(value=self.SubnetId, comparison="EQUALS")  # type: ignore[attr-defined]
                ],
            ),
        )


class VpcModelMixin:
    """
    A mixin is used on :py:class:`botocraft.services.ec2.Vpc` to add
    miscellaneous methods to the class that are not normally part of the
    object.
    """

    @property
    def vulnerabilities(self) -> List["Finding"]:
        """
        Return a list of vulnerabilities for the instance.  This is a
        convenience method to get the vulnerabilities for the instance.

        Returns:
            A list of :py:class:`Finding` objects.

        """
        from botocraft.services import FilterCriteria, Finding, StringFilter

        return Finding.objects.using(self.session).list(  # type: ignore[attr-defined]
            filterCriteria=FilterCriteria(
                ec2InstanceVpcId=[
                    StringFilter(value=self.VpcId, comparison="EQUALS")  # type: ignore[attr-defined]
                ],
            ),
        )
