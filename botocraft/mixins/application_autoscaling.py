from functools import wraps
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from botocraft.services import (
        PutScalingPolicyResponse,
        ScalableTarget,
        ScalingPolicy,
        ScheduledAction,
        Service,
    )

# ----------
# Decorators
# ----------


def scaling_policy_only(
    func: Callable[..., "PutScalingPolicyResponse"],
) -> Callable[..., "ScalingPolicy"]:
    """
    Wraps application-autoscaling put_scaling_policy methods to return the
    actual :py:class:`botocraft.services.application_autoscaling.ScalingPolicy`
    object instead of the response object.
    """

    @wraps(func)
    def wrapper(*args, **_) -> "ScalingPolicy":
        self = args[0]
        policy = args[1]
        func(*args, **_)
        return self.get(
            PolicyNames=[policy.PolicyName],
            ServiceNamespace=policy.ServiceNamespace,
        )

    return wrapper


def scalable_target_only(
    func: Callable[..., "str"],
) -> Callable[..., "ScalableTarget"]:
    """
    Wraps application-autoscaling register_scalable_target methods to return the
    actual :py:class:`botocraft.services.application_autoscaling.ScalableTarget`
    object instead of the ARN.
    """

    @wraps(func)
    def wrapper(*args, **_) -> "ScalableTarget":
        self = args[0]
        target = args[1]
        func(*args, **_)
        return self.get(
            ServiceNamespace=target.ServiceNamespace,
            ResourceIds=[target.ResourceId],
            ScalableDimension=target.ScalableDimension,
        )

    return wrapper


def scheduled_action_only(
    func: Callable[..., None],
) -> Callable[..., "ScheduledAction"]:
    """
    Wraps application-autoscaling put_scheduled_action methods to return the
    actual :py:class:`botocraft.services.application_autoscaling.ScalableTarget`
    object instead of the ARN.
    """

    @wraps(func)
    def wrapper(*args, **_) -> "ScheduledAction":
        self = args[0]
        action = args[1]
        func(*args, **_)
        return self.get(
            ServiceNamespace=action.ServiceNamespace,
            ScalableActionnamese=[action.ScalableActionName],
        )

    return wrapper


# ----------
# Mixins
# ----------


class ScalableTargetModelMixin:
    """
    A mixin class that extends
    :py:class:`~botocraft.services.application_autoscaling.ScalableTarget`.
    """

    @property
    def resource(self) -> "Service":
        """
        Return the resource object for this scalable target.

        Currently only the ``ecs`` service namespace is supported, which
        returns an :py:class:`~botocraft.services.ecs.Service` object.
        """
        from botocraft.services import Service

        _, cluster, service = self.ResourceId.split("/")  # type: ignore[attr-defined]
        if self.ServiceNamespace == "ecs":  # type: ignore[attr-defined]
            return Service.objects.get(service, cluster=cluster)
        msg = f"ServiceNamespace {self.ServiceNamespace} is not supported yet."  # type: ignore[attr-defined]
        raise NotImplementedError(msg)
