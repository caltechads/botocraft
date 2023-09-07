from typing import Callable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from botocraft.services import Service


def ecs_services_only(func: Callable[..., List[str]]) -> Callable[..., List["Service"]]:
    """
    Decorator to convert a list of ECS service ARNs to a list of
    :py:class:`botocraft.services.ecs.Service` objects.
    """
    def wrapper(self, *args, **kwargs) -> List["Service"]:
        arns = func(self, *args, **kwargs)
        services = []
        for i in range(0, len(arns), 100):
            services.extend(
                self.get_many(
                    arns[i:i + 100],
                    cluster=kwargs['cluster'],
                    include=['TAGS']
                )
            )
        return services
    return wrapper
