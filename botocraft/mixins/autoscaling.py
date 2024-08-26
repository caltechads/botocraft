from functools import cached_property
from collections import OrderedDict
import time
from typing import ClassVar, List, TYPE_CHECKING

from botocraft.services.ec2 import Instance

if TYPE_CHECKING:
    from botocraft.services import AutoScalingGroupManager


class AutoScalingGroupModelMixin:
    """
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

    MinSize: int
    MaxSize: int

    @cached_property
    def ec2_instances(self) -> List["Instance"]:
        """
        Return the :py:class:`Instance` objects that belong to this group, if any.
        """
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
