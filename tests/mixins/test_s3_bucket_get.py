from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from botocraft.services import Tag  # must load before botocraft.mixins.s3 (circular)

BUCKET = "my-bucket"


def _manager(listed: list[dict], tags_error: ClientError | None = None) -> MagicMock:
    """Return a stand-in manager that runs ``BucketManagerMixin.get`` without AWS."""
    from botocraft.mixins.s3 import BucketManagerMixin

    class FakeManager(BucketManagerMixin):
        def __init__(self) -> None:
            self.session = MagicMock()
            self.client = MagicMock()
            self.client.exceptions.ClientError = ClientError
            self.client.list_buckets.return_value = {"Buckets": listed}
            self.client.get_bucket_versioning.return_value = {"Status": "Enabled"}
            self.client.get_bucket_ownership_controls.return_value = {
                "Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]
            }

        def get_tags(self, Bucket: str) -> list[Tag]:  # noqa: N803, ARG002
            if tags_error:
                raise tags_error
            return [Tag(Key="team", Value="x")]

        def _get_bucket_logging_configuration(self, _name: str) -> None:
            return None

        def _get_cors_rules(self, _name: str) -> list:
            return []

    return FakeManager()  # type: ignore[return-value]


def _listed() -> list[dict]:
    return [
        {
            "Name": BUCKET,
            "BucketRegion": "us-west-2",
            "CreationDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
        }
    ]


def test_get_missing_bucket_raises_does_not_exist() -> None:
    manager = _manager([])

    with pytest.raises(manager.DoesNotExist, match=BUCKET):
        manager.get(BUCKET)


def test_get_returns_bucket_with_tags() -> None:
    bucket = _manager(_listed()).get(BUCKET)

    assert bucket.BucketName == BUCKET
    assert [(t.Key, t.Value) for t in bucket.Tags] == [("team", "x")]


def test_get_untagged_bucket_has_empty_tags() -> None:
    err = ClientError(
        {"Error": {"Code": "NoSuchTagSet", "Message": "NoSuchTagSet"}},
        "GetBucketTagging",
    )

    bucket = _manager(_listed(), tags_error=err).get(BUCKET)

    assert bucket.Tags == []


def test_get_reraises_other_tag_errors() -> None:
    err = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "AccessDenied"}},
        "GetBucketTagging",
    )

    with pytest.raises(ClientError):
        _manager(_listed(), tags_error=err).get(BUCKET)
