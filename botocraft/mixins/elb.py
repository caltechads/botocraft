# mypy: disable-error-code="attr-defined"
import warnings
from typing import TYPE_CHECKING, Dict, Optional

import boto3

if TYPE_CHECKING:
    from botocraft.services import ClassicELB


class ClassicELBManagerMixin:
    """
    A mixin is used on :py:class:`botocraft.services.elasticache.CacheCluster`
    implement the "security_groups" relation.   Normally we would use a
    "relation" type in the model definition to use the .list() function to list
    what we want, but ``describe_cache_clusters`` either lists a single cluster
    or all clusters, so we need to roll our own method
    """

    session: boto3.session.Session

    def create(
        self,
        elb: "ClassicELB",
        Tags: Optional[Dict[str, str]] = None,  # noqa: N803
    ) -> "ClassicELB":
        """
        Create a new :py:class:`ClassicELB` object.  The reason we have to do this
        in a mixin instead of having this as a usual ``.create()`` method automatically
        generated is because Classic ELBs are fragmented across multiple API calls.

        We want to pretend that the Classic ELB is a single object, so we have to
        deal with the fragmentation here.

        Args:
            elb: The :py:class:`ClassicELB` object to create

        Keyword Args:
            Tags: A dictionary of tags to apply to the ELB

        Returns:
            The newly created :py:class:`ClassicELB` object

        """
        if Tags:
            tags = [{"Key": key, "Value": value} for key, value in Tags.items()]
        self.client.create_load_balancer(
            LoadBalancerName=elb.LoadBalancerName,
            Listeners=self.serialize(
                [listener.Listeners for listener in elb.Listeners]
            ),
            AvailabilityZones=elb.AvailabilityZones,
            Subnets=elb.Subnets,
            SecurityGroups=elb.SecurityGroups,
            Scheme=elb.Scheme,
            Tags=tags if Tags else None,
        )

        if elb.HealthCheck:
            self.client.configure_health_check(
                LoadBalancerName=elb.LoadBalancerName,
                HealthCheck=self.serialize(elb.HealthCheck),
            )

        if elb.Policies:
            if elb.Policies:
                if elb.Policies.AppCookieStickinessPolicies:
                    self.client.create_app_cookie_stickiness_policy(
                        LoadBalancerName=elb.LoadBalancerName,
                        PolicyName=elb.Policies.AppCookieStickinessPolicies[
                            0
                        ].PolicyName,
                        CookieName=elb.Policies.AppCookieStickinessPolicies[
                            0
                        ].CookieName,
                    )
                if elb.Policies.LBCookieStickinessPolicies:
                    self.client.create_lb_cookie_stickiness_policy(
                        LoadBalancerName=elb.LoadBalancerName,
                        PolicyName=elb.Policies.LBCookieStickinessPolicies[
                            0
                        ].PolicyName,
                        CookieExpirationPeriod=elb.Policies.LBCookieStickinessPolicies[
                            0
                        ].CookieExpirationPeriod,
                    )
                names = ", ".join([x.PolicyName for x in elb.Policies.OtherPolicies])
                # Warn that these policies must be created via ClassicELB.create_policy
                warnings.warn(
                    f"ClassicELB(LoadBalancerName='{elb.LoadBalancerName}'): "
                    "These polices must be created via ClassicELB.create_policy: "
                    f"{names}",
                    UserWarning,
                    stacklevel=2,
                )
