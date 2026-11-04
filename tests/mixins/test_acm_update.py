from unittest.mock import MagicMock

from botocraft.services.common import Tag

ARN = "arn:aws:acm:us-west-2:000000000000:certificate/example"


def _manager(existing_tags: list[dict[str, str]]) -> MagicMock:
    """Return a stand-in manager that runs the mixin without AWS."""
    # Imported here: botocraft.mixins.acm must load after botocraft.services.
    from botocraft.mixins.acm import ACMManagerMixin

    class FakeManager(ACMManagerMixin):
        def __init__(self) -> None:
            self.client = MagicMock()
            self.client.list_tags_for_certificate.return_value = {"Tags": existing_tags}

    return FakeManager()  # type: ignore[return-value]


def _model(tags: list[Tag] | None) -> MagicMock:
    model = MagicMock()
    model.CertificateArn = ARN
    model.Tags = tags
    return model


def test_update_replaces_tags_with_plain_dicts() -> None:
    manager = _manager([{"Key": "old", "Value": "1"}])

    manager.update(_model([Tag(Key="team", Value="x")]))

    manager.client.remove_tags_from_certificate.assert_called_once_with(
        CertificateArn=ARN, Tags=[{"Key": "old", "Value": "1"}]
    )
    manager.client.add_tags_to_certificate.assert_called_once_with(
        CertificateArn=ARN, Tags=[{"Key": "team", "Value": "x"}]
    )


def test_update_skips_empty_tag_calls() -> None:
    manager = _manager([])

    manager.update(_model(None))

    manager.client.remove_tags_from_certificate.assert_not_called()
    manager.client.add_tags_to_certificate.assert_not_called()
