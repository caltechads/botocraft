from functools import cached_property
from collections import OrderedDict
from typing import List

from botocraft.services.ec2 import Instance


class AutoScalingGroupInstancesMixin:
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
