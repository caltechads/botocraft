from unittest.mock import MagicMock

import pytest

import botocraft.services  # noqa: F401  must load before botocraft.mixins.s3 (circular)

TARGET = {"TargetBucket": "logs", "TargetPrefix": "p/"}


def _logging(config: dict):
    from botocraft.mixins.s3 import BucketManagerMixin

    class FakeManager(BucketManagerMixin):
        def __init__(self) -> None:
            self.client = MagicMock()
            self.client.get_bucket_logging.return_value = config

    return FakeManager()._get_bucket_logging_configuration("b")  # noqa: SLF001


def test_logging_disabled():
    assert _logging({}) is None


def test_simple_prefix_only():
    """Regression: KeyError 'PartitionedPrefix' when only SimplePrefix is returned."""
    result = _logging(
        {"LoggingEnabled": {**TARGET, "TargetObjectKeyFormat": {"SimplePrefix": {}}}}
    )
    fmt = result.TargetObjectKeyFormat
    assert fmt.SimplePrefix is not None
    assert fmt.PartitionedPrefix is None


@pytest.mark.parametrize("source", ["EventTime", None])
def test_partitioned_prefix_only(source):
    part = {"PartitionDateSource": source} if source else {}
    result = _logging(
        {
            "LoggingEnabled": {
                **TARGET,
                "TargetObjectKeyFormat": {"PartitionedPrefix": part},
            }
        }
    )
    fmt = result.TargetObjectKeyFormat
    assert fmt.SimplePrefix is None
    assert fmt.PartitionedPrefix.PartitionDateSource == source


def test_grantee_without_email_or_id():
    """Group grantees carry only Type and URI."""
    grant = {
        "Grantee": {
            "Type": "Group",
            "URI": "http://acs.amazonaws.com/groups/s3/LogDelivery",
        },
        "Permission": "WRITE",
    }
    result = _logging({"LoggingEnabled": {**TARGET, "TargetGrants": [grant]}})
    assert result.TargetGrants[0].Grantee.EmailAddress is None
    assert result.TargetGrants[0].Grantee.ID is None
