from types import SimpleNamespace

from botocraft.eventbridge.common import event_summary


def test_event_summary_accepts_event_and_event_name_details() -> None:
    """
    Detail fields called ``event`` or ``event_name`` must not collide with the
    function's own positional parameters.
    """
    metadata = SimpleNamespace(
        account="000000000000",
        source="aws.es",
        time="2026-01-01T00:00:00Z",
        region="us-west-2",
        resources=["arn:aws:es:us-west-2:000000000000:domain/example"],
    )

    summary = event_summary(
        "OpenSearch Software Update Notification",
        metadata,
        event="SOFTWARE_UPDATE",
        event_name="DescribeDomain",
    )

    assert "SOFTWARE_UPDATE" in summary
    assert "DescribeDomain" in summary
    assert "OpenSearch Software Update Notification" in summary
