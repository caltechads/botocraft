from unittest.mock import MagicMock

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.docdb import (
    DocDBClusterParameterGroup,
    DocDBClusterParameterGroupManager,
)

ARN = "arn:aws:rds:us-west-2:000000000000:cluster-pg:example"


def _group(name: str = "example") -> DocDBClusterParameterGroup:
    return DocDBClusterParameterGroup(
        DBClusterParameterGroupName=name,
        DBParameterGroupFamily="docdb5.0",
        Description="example",
        DBClusterParameterGroupArn=ARN,
    )


def _manager(describe_pages: list[dict]) -> DocDBClusterParameterGroupManager:
    manager = DocDBClusterParameterGroupManager.__new__(
        DocDBClusterParameterGroupManager
    )
    manager.client = MagicMock()
    manager.session = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = describe_pages
    manager.client.get_paginator.return_value = paginator
    manager.client.list_tags_for_resource.return_value = {
        "TagList": [{"Key": "team", "Value": "x"}]
    }
    return manager


def test_generated_model_has_the_shape_fields_and_tags() -> None:
    group = _group()

    assert group.DBClusterParameterGroupName == "example"
    assert group.DBParameterGroupFamily == "docdb5.0"
    assert group.DBClusterParameterGroupArn == ARN
    assert group.Tags == []


def test_list_returns_typed_groups_with_tags_populated() -> None:
    page = {
        "DBClusterParameterGroups": [
            {
                "DBClusterParameterGroupName": "example",
                "DBParameterGroupFamily": "docdb5.0",
                "Description": "example",
                "DBClusterParameterGroupArn": ARN,
            }
        ]
    }
    manager = _manager([page])

    result = manager.list()

    assert isinstance(result, PrimaryBoto3ModelQuerySet)
    groups = list(result)
    assert [g.DBClusterParameterGroupName for g in groups] == ["example"]
    manager.client.list_tags_for_resource.assert_called_once_with(ResourceName=ARN)
    assert groups[0].Tags is not None
    assert groups[0].Tags[0].Key == "team"


def test_update_modifies_then_returns_the_refreshed_group() -> None:
    from botocraft.services.docdb import DocDBParameter

    describe = {
        "DBClusterParameterGroups": [
            {
                "DBClusterParameterGroupName": "example",
                "DBParameterGroupFamily": "docdb5.0",
                "Description": "refreshed",
                "DBClusterParameterGroupArn": ARN,
            }
        ]
    }
    manager = _manager([describe])
    manager.client.describe_db_cluster_parameter_groups.return_value = describe
    params = [
        DocDBParameter(
            ParameterName="tls", ParameterValue="disabled", ApplyMethod="pending-reboot"
        )
    ]

    result = manager.update(_group(), params)

    manager.client.modify_db_cluster_parameter_group.assert_called_once()
    kwargs = manager.client.modify_db_cluster_parameter_group.call_args.kwargs
    assert kwargs["DBClusterParameterGroupName"] == "example"
    assert kwargs["Parameters"][0]["ParameterName"] == "tls"
    assert isinstance(result, DocDBClusterParameterGroup)
    assert result.Description == "refreshed"
    assert result.Tags
