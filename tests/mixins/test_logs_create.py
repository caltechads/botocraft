from unittest.mock import MagicMock


def test_create_log_group_extended_forwards_tags_and_returns_none() -> None:
    """
    The wrapper must accept ``tags`` (the generated ``create`` signature has it)
    and pass it on to the wrapped function.
    """
    # Imported here: botocraft.mixins.logs must load after botocraft.services.
    import botocraft.services.logs  # noqa: F401
    from botocraft.mixins.logs import create_log_group_extended

    inner = MagicMock(return_value=None)
    manager = MagicMock()
    model = MagicMock()
    model.Tags = None

    result = create_log_group_extended(inner)(manager, model, {"team": "x"})

    assert result is None
    inner.assert_called_once_with(manager, model, {"team": "x"})
    manager.client.tag_log_group.assert_called_once()
    assert manager.client.tag_log_group.call_args.kwargs["tags"] == []
