from typing import TYPE_CHECKING, Callable, List, Literal, Optional, cast

if TYPE_CHECKING:
    from botocraft.services import (
        Instance,
        Reservation,
        Tag,
        TagSpecification,
    )


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


# -------------
# Mixin classes
# -------------


class EC2TagsManagerMixin:
    """
    A mixin is used on on :py:class:`botocraft.services.ec2.InstanceManager`
    to convert the odd EC2 tag list to a :py:class:`TagSpecification` object.
    """

    def convert_tags(
        self, tags: Optional[List["Tag"]], resource_type: ResourceType
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
            self.objects.authorize_ingress(group_id, self.IpPermissions, **kwargs)
        else:
            old_obj = self.objects.get(self.pk)
            if self.IpPermissions != old_obj.IpPermissions:
                if old_obj.IpPermissions:
                    self.objects.revoke_ingress(
                        self.pk, old_obj.IpPermissions, **kwargs
                    )
                if self.IpPermissions:
                    self.objects.authorize_ingress(
                        self.pk, self.IpPermissions, **kwargs
                    )


# ----------
# Decorators
# ----------


def ec2_instances_only(
    func: Callable[..., List["Reservation"]],
) -> Callable[..., List["Instance"]]:
    """
    Wraps a boto3 method that returns a list of :py:class:`Reservation` objects
    to return a list of :py:class:`Instance` objects instead.
    """

    def wrapper(*args, **kwargs) -> List["Instance"]:
        reservations = func(*args, **kwargs)
        instances: List["Instance"] = []  # noqa: UP037
        for reservation in reservations:
            instances.extend(cast(List["Instance"], reservation.Instances))
        return instances

    return wrapper


def ec2_instance_only(
    func: Callable[..., Optional["Reservation"]],
) -> Callable[..., Optional["Instance"]]:
    """
    Wraps a boto3 method that returns a list of :py:class:`Reservation` objects
    to return a single :py:class:`Instance` object instead.
    """

    def wrapper(*args, **kwargs) -> Optional["Instance"]:
        reservation = func(*args, **kwargs)
        if not reservation:
            return None
        return cast(List["Instance"], reservation.Instances)[0]

    return wrapper
