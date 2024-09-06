from functools import cached_property
from collections import OrderedDict
import time
from typing import ClassVar, List, TYPE_CHECKING

from botocore.exceptions import WaiterError

if TYPE_CHECKING:
    from botocraft.services import (
        AutoScalingGroupManager,
        Instance,
    )


class AutoScalingGroupModelMixin:
    """
    This is a mixin for :py:class:`AutoScalingGroup` that adds some convenience
    methods.

    Sometimes we like full :py:class:`Instance` objects instead of the
    :py:class:`AutoScalingInstanceReference` objects that get listed on
    :py:attr:`AutoScalingGroup.Instances`.

    EC2 is weird and doesn't have an easy way to list instances in an
    autoscaling group except to use one of the ``Filter`` parameters on
    ``describe_instances``.  Instances that are part of an autoscaling group
    have a tag called ``aws:autoscaling:groupName`` whose value is the name of
    the autoscaling group.  We can use this to filter instances that belong to a
    particular autoscaling group.

    This method is too specialized at the moment to be included as one of the
    transformers for model related objects, so we'll just add it as a mixin.
    """

    objects: ClassVar["AutoScalingGroupManager"]

    AutoScalingGroupName: str
    MinSize: int
    MaxSize: int

    @cached_property
    def ec2_instances(self) -> List["Instance"]:
        """
        Return the :py:class:`Instance` objects that belong to this group, if any.
        """
        # Avoid circular import
        from botocraft.services.ec2 import Instance  # pylint: disable=import-outside-toplevel
        if self.AutoScalingGroupName:  # type: ignore
            pk = OrderedDict(
                Filters=[
                    {
                        'Name': 'tag:aws:autoscaling:groupName',
                        'Values': [self.AutoScalingGroupName]  # type: ignore
                    }
                ]
            )
            return Instance.objects.list(**pk)
        else:
            return []

    @property
    def is_stable(self) -> bool:
        """
        Return ``True`` if the autoscaling group is stable, ``False`` otherwise.

        An autoscaling group is considered stable if all instances are running
        and healthy and the DesiredCapacity is equal to the number of instances.
        """
        ec2_instances = self.ec2_instances
        if len(ec2_instances) == self.DesiredCapacity:
            # check if all instances are in service
            instance_ids = [instance.InstanceId for instance in ec2_instances]
            details = self.objects.instance_status(
                InstanceIds=instance_ids
            )
            if all(detail.HealthStatus == 'HEALTHY' for detail in details):
                return True
        return False

    def wait_until_stable(
        self,
        max_attempts: int = 40,
        delay: int = 15
    ) -> None:
        """
        Since there is no waiter for this, we'll use this method to wait until
        the autoscaling group is stable.

        Raises:
            botocore.exceptions.WaiterError: If the autoscaling group is not
                stable after ``max_attempts``.

        Keyword Args:
            max_attempts: The maximum number of attempts to make before giving
                up.
            delay: The number of seconds to wait between attempts.
        """
        from botocraft.services import AutoScalingGroupsType  # pylint: disable=import-outside-toplevel
        wait_count: int = 0
        # There is no waiter for this, so we'll just poll until the desired
        # count is reached, or we reach max_attempts.
        while True:
            asg = self.objects.get(AutoScalingGroupName=self.AutoScalingGroupName)
            assert asg is not None, "AutoScalingGroup.wait_until_stable(): Autoscaling group not found."
            if wait_count >= max_attempts:
                reason = 'Max attempts exceeded'
                raise WaiterError(
                    name='asg_stable',
                    reason=reason,
                    last_response=AutoScalingGroupsType(AutoScalingGroups=[asg]).model_dump(),  # type: ignore
                )
            if asg.is_stable:
                break
            wait_count += 1
            time.sleep(delay)

    def scale(
        self,
        desired_count: int,
        wait: bool = False,
        max_attempts: int = 40,
    ) -> None:
        """
        Scale the autoscaling group to the desired count.

        Args:
            desired_count: The number of tasks to run.

        Keyword Args:
            wait: If True, wait for the service to reach the desired count.
        """
        if desired_count < self.MinSize:
            raise ValueError(
                f"desired_count must be greater than or equal to MinSize, which is {self.MinSize}."
            )
        if desired_count > self.MaxSize:
            raise ValueError(
                f"desired_count must be less than or equal to MaxSize, which is {self.MaxSize}."
            )
        self.save()  # type: ignore[attr-defined]
        time.sleep(10)
        if wait:
            wait_count: int = 0
            # There is no waiter for this, so we'll just poll until the desired
            # count is reached, or we reach max_attempts.
            while True:
                if wait_count >= max_attempts:
                    raise TimeoutError(
                        f"Reached max attempts of {max_attempts} to reach desired count of {desired_count}."
                    )
                if len(self.ec2_instances) == desired_count:
                    # check if all instances are in service
                    if all(instance.State.Name == 'running' for instance in self.ec2_instances):
                        instance_ids = [instance.InstanceId for instance in self.ec2_instances]
                        details = self.objects.instance_status(
                            InstanceIds=instance_ids
                        )
                        if all(detail.HealthStatus == 'Healthy' for detail in details):
                            break
                wait_count += 1
                time.sleep(5)
