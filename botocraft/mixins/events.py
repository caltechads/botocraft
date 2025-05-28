# mypy: disable-error-code="attr-defined"
from functools import wraps
from typing import TYPE_CHECKING, Callable, List, Optional

if TYPE_CHECKING:
    from botocraft.services import DescribeRuleResponse, EventBus, EventRule
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet


def event_rules_only(
    func: Callable[..., List[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.events.EventRuleManager.list_by_target`
    to return :py:class:`botocraft.services.ecs.EventRule` objects instead of
    only a list of Rule names.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        names = func(self, *args, **kwargs)
        events = [self.get(name) for name in names]
        return PrimaryBoto3ModelQuerySet(events)

    return wrapper


def DescribeRuleResponse_to_EventRule(
    func: Callable[..., Optional["DescribeRuleResponse"]],
) -> Callable[..., Optional["EventRule"]]:
    """
    The boto3 call describe_rule does not actually return a rule object, but
    instead a DescribeRuleResponse object. This decorator wraps the function
    to return a Rule object instead.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Optional["EventRule"]:
        from botocraft.services import EventRule

        response = func(self, *args, **kwargs)
        if not response:
            return None
        rule = EventRule(**response.model_dump())
        self.sessionize(rule)
        return rule

    return wrapper


def EventRule_purge_CreatedBy_attribute(
    func: Callable[..., str],
) -> Callable[..., str]:
    """
    The boto3 call describe_rule does not actually return a rule object, but
    instead a DescribeRuleResponse object. This decorator wraps the function
    to return a Rule object instead.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> str:
        model = args[0]
        model.CreatedBy = None
        return func(self, *args, **kwargs)

    return wrapper


def DescribeEventBusResponse_to_EventBus(
    func: Callable[..., Optional["DescribeRuleResponse"]],
) -> Callable[..., Optional["EventBus"]]:
    """
    The boto3 call describe_rule does not actually return a rule object, but
    instead a DescribeRuleResponse object. This decorator wraps the function
    to return a Rule object instead.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Optional["EventRule"]:
        from botocraft.services.events import EventBus

        response = func(self, *args, **kwargs)
        if not response:
            return None
        bus = EventBus(**response.model_dump())
        self.sessionize(bus)
        return bus  # type: ignore[return-value]

    return wrapper  # type: ignore[return-value]
