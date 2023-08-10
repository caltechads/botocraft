from typing import List, Literal, Optional

import boto3
from botocraft.models import Service


class ServiceManager:
    service_name = "ecs"

    def __init__(self) -> None:
        self.client = boto3.client(self.service_name)

    def create(self, model: Service) -> None:
        pass

    def get(
        self,
        services: List[str],
        cluster: Optional[str] = None,
        include: Optional[List[Literal["TAGS"]]] = None,
    ) -> None:
        pass

    def update(self, model: Service) -> None:
        pass

    def delete(
        self, service: str, cluster: Optional[str] = None, force: Optional[bool] = None
    ) -> None:
        pass

    def list(
        self,
        cluster: Optional[str] = None,
        nextToken: Optional[str] = None,
        maxResults: Optional[int] = None,
        launchType: Optional[Literal["EC2", "FARGATE", "EXTERNAL"]] = None,
        schedulingStrategy: Optional[Literal["REPLICA", "DAEMON"]] = None,
    ) -> None:
        pass
