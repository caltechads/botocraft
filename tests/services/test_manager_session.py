"""Session binding for Boto3ModelManager.using."""

from __future__ import annotations

import threading
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, cast
from unittest.mock import MagicMock

from botocraft.services.abstract import Boto3ModelManager, PrimaryBoto3Model

if TYPE_CHECKING:
    import boto3


class FakeSession:
    """Stand-in session. ``client()`` returns one stable fake client."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.built = MagicMock(name=f"client-{name}")
        self.built.marker = name

    def client(self, service_name: str) -> MagicMock:
        self.built.service_name = service_name
        return self.built


class ProbeManager(Boto3ModelManager):
    """Manager double. Does not construct a real boto3 client."""

    service_name = "sts"
    invoked: ClassVar[list[Any]] = []

    def __init__(self) -> None:
        # Do not call Boto3ModelManager.__init__. That builds a real client.
        self.client = MagicMock(name="default-client")
        self.client.marker = "default"
        self.session = None  # type: ignore[assignment]

    def get(self, name: str) -> str:
        self.client.invoke(name)
        self.invoked.append(self.client)
        return name

    def update(self, model: Any, **_kwargs: Any) -> Any:
        self.client.invoke("update")
        self.invoked.append(self.client)
        return model

    def create(self, model: Any, **_kwargs: Any) -> Any:
        self.client.invoke("create")
        self.invoked.append(self.client)
        return model

    def delete(self, pk: str, **_kwargs: Any) -> str:
        self.client.invoke("delete")
        self.invoked.append(self.client)
        return pk


class SessionLabelManager(ProbeManager):
    """Probe whose cached label is the bound session name."""

    @cached_property
    def session_label(self) -> str:
        """Return ``session.name``, or ``none`` when no session is bound."""
        if self.session is None:
            return "none"
        return self.session.name  # type: ignore[attr-defined]


def _as_session(session: FakeSession) -> boto3.session.Session:
    return cast("boto3.session.Session", session)


def test_using_does_not_mutate_the_receiver() -> None:
    shared = ProbeManager()
    original = shared.client
    session_a = FakeSession("a")
    session_b = FakeSession("b")

    bound_a = shared.using(_as_session(session_a))
    bound_b = shared.using(_as_session(session_b))
    bound_a.get("alpha")

    assert bound_a is not shared
    assert bound_b is not shared
    assert bound_a is not bound_b
    assert shared.client is original
    assert bound_a.client is session_a.built
    assert bound_b.client is session_b.built
    assert bound_a.session is session_a
    assert shared.session is None
    assert session_a.built.service_name == "sts"
    session_a.built.invoke.assert_called_once_with("alpha")
    session_b.built.invoke.assert_not_called()
    original.invoke.assert_not_called()


def test_using_recomputes_cached_properties_for_the_new_session() -> None:
    shared = SessionLabelManager()
    session_a = FakeSession("a")
    session_b = FakeSession("b")
    shared.session = _as_session(session_a)
    assert shared.session_label == "a"

    bound = shared.using(_as_session(session_b))

    assert bound.session_label == "b"
    assert shared.session_label == "a"


def test_using_none_returns_the_same_manager() -> None:
    shared = ProbeManager()
    original = shared.client
    assert shared.using(None) is shared
    assert shared.client is original


def test_later_using_does_not_change_an_earlier_bound_manager() -> None:
    shared = ProbeManager()
    session_a = FakeSession("a")
    session_b = FakeSession("b")
    bound_a = shared.using(_as_session(session_a))
    shared.using(_as_session(session_b))
    bound_a.get("alpha")
    assert bound_a.client is session_a.built
    session_a.built.invoke.assert_called_once_with("alpha")


def test_using_is_isolated_across_threads() -> None:
    shared = ProbeManager()
    original = shared.client
    sessions = [FakeSession("a"), FakeSession("b")]
    barrier = threading.Barrier(2)
    errors: list[object] = []

    def worker(session: FakeSession) -> None:
        try:
            for _ in range(50):
                barrier.wait(timeout=5)
                bound = shared.using(_as_session(session))
                bound.get(session.name)
                if bound.client is not session.built:
                    errors.append(("client", session.name))
                if shared.client is not original:
                    errors.append("receiver")
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(session,)) for session in sessions]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert errors == []
    assert not any(thread.is_alive() for thread in threads)
    for session in sessions:
        assert session.built.invoke.call_count == 50


class Probe(PrimaryBoto3Model):
    """Tiny primary model whose manager records the client each call used."""

    manager_class: ClassVar[type[Boto3ModelManager]] = ProbeManager
    widget_id: str | None = None

    @property
    def pk(self) -> str | None:
        return self.widget_id


def test_save_update_uses_model_session() -> None:
    ProbeManager.invoked = []
    session = FakeSession("role")
    model = Probe(widget_id="widget")
    model.session = session
    model.save()
    assert ProbeManager.invoked == [session.built]


def test_save_create_uses_model_session() -> None:
    ProbeManager.invoked = []
    session = FakeSession("role")
    model = Probe(widget_id=None)
    model.session = session
    model.save()
    assert ProbeManager.invoked == [session.built]


def test_delete_uses_model_session() -> None:
    ProbeManager.invoked = []
    session = FakeSession("role")
    model = Probe(widget_id="widget")
    model.session = session
    model.delete()
    assert ProbeManager.invoked == [session.built]


def test_save_without_session_uses_the_default_client() -> None:
    ProbeManager.invoked = []
    model = Probe(widget_id="widget")
    assert model.session is None
    model.save()
    assert [client.marker for client in ProbeManager.invoked] == ["default"]


def test_security_group_create_uses_model_session() -> None:
    from botocraft.mixins.ec2 import SecurityGroupModelMixin

    log: list[tuple[str, object]] = []
    session = FakeSession("role")

    class RecordingManager:
        def __init__(self) -> None:
            self.session: object | None = None

        def using(self, bound_session: object) -> RecordingManager:
            child = RecordingManager()
            child.session = bound_session
            return child

        def create(self, _model: object, **_kwargs: object) -> str:
            log.append(("create", self.session))
            return "sg-1"

        def authorize_ingress(
            self, _group_id: str, _permissions: object, **_kwargs: object
        ) -> None:
            log.append(("ingress", self.session))

    target = type("SG", (), {})()
    target.pk = None
    target.session = session
    target.IpPermissions = ["perm"]
    target.objects = RecordingManager()
    SecurityGroupModelMixin.save(target)
    assert log == [("create", session), ("ingress", session)]


def test_bind_manager_session_returns_the_bound_manager() -> None:
    from botocraft.datasync import _bind_manager_session

    session = FakeSession("role")
    manager = ProbeManager()
    original = manager.client
    bound = _bind_manager_session(manager, _as_session(session))
    assert bound is not manager
    assert bound.client is session.built
    assert manager.client is original


def test_bind_manager_session_none_returns_the_same_manager() -> None:
    from botocraft.datasync import _bind_manager_session

    manager = ProbeManager()
    assert _bind_manager_session(manager, None) is manager
