# pylint: disable=expression-not-assigned,pointless-statement,line-too-long
from typing import Literal

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import User
from diagrams.aws.analytics import ES
from diagrams.aws.compute import ECS
from diagrams.aws.database import RDSMysqlInstance, ElasticacheForRedis
from diagrams.aws.network import (
    ALB,
    InternetGateway,
    VPCPeering,
    VPC as AWSVPC
)
from diagrams.aws.storage import EFS


default_graph_attr = {
    "layout": "dot",
    "compound": "true",
    "splines": "true",
}


class VPC(Cluster):
    """
    Make a ``Cluster`` subclass that just sets the title and background
    color based on what account the VPC is in.

    Args:
        title: the name of the VPC
        account: the human name of the account the VPC is in
    """

    def __init__(
        self,
        title: str = "",
        account: str = "",
        **kwargs
    ):
        kwargs.setdefault("direction", "LR")  # Set direction Left to Right
        if account:
            title = f"{title}\nAccount: {account}"
        if account == "ADS-PROD":
            graph_attr = {"bgcolor": "beige"}
        elif account == "ACS-PROD":
            graph_attr = {"bgcolor": "gray95"}
        else:
            graph_attr = {"bgcolor": "lightblue"}
        graph_attr['penwidth'] = "0.0"
        super().__init__(f"VPC: {title}", graph_attr=graph_attr, **kwargs)


class Subnet(Cluster):
    """
    Subclass ``Cluster`` to represent a VPC Subnet.  This will set the
    background color of the box based on whether the subnet is a public
    or private subnet.

    Args:
        name: the name of the subnet
        scope: either "public" or "private"
    """

    def __init__(
        self,
        name: str,
        scope: Literal["public", "private"] = "private"
    ):
        if scope not in ["public", "private"]:
            raise ValueError('Scope must be either "public" or "private"')

        self.scope = scope
        color = "lightblue" if self.scope == "public" else "lightgrey"
        super().__init__(f"Subnet: {name}", graph_attr={"bgcolor": color})


with Diagram(
    "caltech_docs",
    direction="LR",
    filename="caltech_docs",
    show=False,
    graph_attr=default_graph_attr
):
    igw = InternetGateway("IGW")

    user = User("Human User")

    with Cluster(
        "other",
        graph_attr={"label": "", "bgcolor": "transparent", "penwidth": "0.0"}
    ) as ads_other:
        with Cluster(
            "0",
            graph_attr={"label": "Other VPCs", "bgcolor": "lightblue"}
        ) as ads_prod:
            ac = AWSVPC("")

        peering = VPCPeering("VPC peering connections")

    with VPC("ads-production", account="ACS-PROD") as vpc:
        with Subnet("elb-public", scope="public") as dmz_public:
            proxy_alb = ALB("acproxy-prod")

        with Subnet("prod-proxy-servers-private"):
            proxy = ECS("Service: acproxy-prod")

    with VPC("utils", account="ADS-PROD") as vpc:
        with Subnet("ielb-private", scope="public") as dmz_public:
            alb = ALB("alb")

        with Subnet("prod-apps-private"):
            service = ECS("Service: caltech-docs-prod")

        with Subnet("api-private") as ielb_private:
            api_alb = ALB("internal-api")

        with Subnet("db-private") as db_private:
            rds = RDSMysqlInstance("RDS\nads-prod")
            ec = ElasticacheForRedis("Redis\nads-prod")
            es = ES("OpenSearch\ncaltech-docs")


    user >> igw >> Edge(label="443 (HTTP)\naccess.caltech.edu", color="green", penwidth="2.0") >> proxy_alb >> Edge(label="443 (HTTP)", color="green", penwidth="2.0") >> proxy
    proxy >> Edge(label="443 (HTTPS)", color="green", penwidth="2.0") >> peering >> Edge(label="443 (HTTPS)\n/caltech_docs/*\n/static/caltech_docs/*", color="green", penwidth="2.0") >> alb
    alb >> Edge(label="443 (HTTPS)\n/caltech_docs/*\n/static/caltech_docs/*", color="green", penwidth="2.0") >> service
    service >> rds
    service >> ec
    service >> es
    ac >> Edge(ltail="cluster_0", label="443 (HTTPS)", color="red", penwidth="2.0") >> peering
    peering >> Edge(label="443 (HTTP)\ncaltech-docs-prod.ac.api.ads.caltech.internal", color="red", penwidth="2.0") >> api_alb

    api_alb >> Edge(label="443 (HTTPS)\n/api/*", color="red", penwidth="2.0") >> service