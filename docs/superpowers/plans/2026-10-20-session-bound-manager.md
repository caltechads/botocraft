# Session-Bound Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Boto3ModelManager.using(session)` return a new manager whose client comes from that session, without changing the receiver, and make top-level `save()` / `delete()` use the session stamped on the model.

**Architecture:** `using(session)` shallow-copies the receiver, then replaces `session` and `client` on the copy. `using(None)` returns the receiver. `PrimaryBoto3Model.save` and `delete` call `self.objects.using(self.session)`. `sessionize` is left as it is, so only the top-level primary model carries the session. No context manager, lock, or `contextvar`.

**Tech Stack:** Python 3.10+, boto3, pydantic, pytest, ruff, mypy. Commands use `.venv/bin/pytest`, `.venv/bin/ruff`, and `.venv/bin/mypy`.

**Spec:** `docs/adr/0002-using-returns-a-session-bound-manager.md`

## Out of scope

- Do not run `bumpversion`, `bin/release.sh`, or `twine`. The maintainer publishes.
- Do not add a changelog file. The Task 1 commit message is the release note.
- Do not edit `botocraft/sync/`, `doc/source/api/services/`, or `doc/source/overview/_services_list.rst`.
- Do not edit `botocraft/services/*.py` except `botocraft/services/abstract.py`. That file is handwritten. Sync imports it and does not generate it. `AGENTS.md` forbids editing generated service modules; this file is the exception.
- Do not change `set_session` or `sessionize`.

## File map

- Modify `botocraft/services/abstract.py`: `using`, `save`, `delete`.
- Modify `botocraft/mixins/ec2.py`: `SecurityGroupModelMixin.save` create call only.
- Modify `botocraft/datasync.py`: `_bind_manager_session` must return the manager `using()` returns.
- Create `tests/services/test_manager_session.py`: leak, concurrency, save, delete, security-group create, datasync helper.
- Modify `doc/source/overview/services.rst`: Sessions section.
- Modify `doc/source/overview/ses.rst` and `doc/source/overview/kinesis.rst`: replace the "call using before get" sentences.

---

### Task 1: `using()` returns a new manager

**Files:**
- Create: `tests/services/test_manager_session.py`
- Modify: `botocraft/services/abstract.py` (import line and `Boto3ModelManager.using`, currently lines 126-142)

- [ ] **Step 1: Write the failing tests**

Create `tests/services/test_manager_session.py`:

```python
"""Session binding for Boto3ModelManager.using."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, ClassVar, cast
from unittest.mock import MagicMock

from botocraft.services.abstract import Boto3ModelManager

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
    session_a.built.invoke.assert_called_once_with("alpha")
    session_b.built.invoke.assert_not_called()
    original.invoke.assert_not_called()


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
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `.venv/bin/pytest tests/services/test_manager_session.py -v`

Expected: FAIL. `test_using_does_not_mutate_the_receiver` raises `AssertionError` because `bound_a is shared`. The old `using()` writes `self.client` and returns `self`. Do not change production code in this step.

- [ ] **Step 3: Implement `using()`**

In `botocraft/services/abstract.py`, add `import copy` next to the other stdlib imports.

Replace `Boto3ModelManager.using` with:

```python
def using(self, session: boto3.session.Session | None) -> "Boto3ModelManager":
    """
    Return a manager bound to ``session``.

    The receiver is not modified. Manager methods call ``self.client``, so
    the returned manager's client is built from ``session``. A caller who
    ignores the return value keeps the receiver's existing client.

    Args:
        session: Session to bind. ``None`` means do not rebind.

    Returns:
        This manager when ``session`` is ``None``. Otherwise a new manager
        of the same class that holds ``session`` and
        ``session.client(service_name)``.

    """
    if session is None:
        return self
    # ponytail: shallow copy, then replace session and client.
    # Per-field clone if a manager stores mutable state that must not be shared.
    bound = copy.copy(self)
    bound.session = session
    bound.client = session.client(self.service_name)  # type: ignore[call-overload]
    return bound
```

- [ ] **Step 4: Run the tests and verify they pass**

Run: `.venv/bin/pytest tests/services/test_manager_session.py -v`

Expected: PASS, 4 tests.

- [ ] **Step 5: Commit**

```bash
git add tests/services/test_manager_session.py botocraft/services/abstract.py
git commit -m "$(cat <<'EOF'
BUGFIX: return a new manager from using() so callers do not share a session.

using(session) used to write session and client on the receiver. A held
manager then ran later calls with whichever session landed last. Callers
that ignore the return value still use the receiver's existing client.

EOF
)"
```

---

### Task 2: `save()` and `delete()` use the model's session

**Files:**
- Modify: `tests/services/test_manager_session.py`
- Modify: `botocraft/services/abstract.py` (`PrimaryBoto3Model.save` around line 396, `delete` around line 411)

- [ ] **Step 1: Add manager methods, then the failing tests**

Do this before appending the tests. `ModelIdentityMixin.name` and `.arn` raise `ValueError` when the stored value is missing. `Probe.pk` must not use those fields. A missing primary key has to be `None` so `save()` can reach `create()`.

Add these methods to `ProbeManager`, next to `get`. They must append `self.client` the same way `get` does. Without them, `save()` fails with `AttributeError` instead of the default-client assertion below.

```python
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
```

Add `PrimaryBoto3Model` to the abstract import, then append:

```python
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
```

- [ ] **Step 2: Run the new tests and verify the session tests fail**

Run: `.venv/bin/pytest tests/services/test_manager_session.py::test_save_update_uses_model_session tests/services/test_manager_session.py::test_save_create_uses_model_session tests/services/test_manager_session.py::test_delete_uses_model_session -v`

Expected: FAIL. `ProbeManager.invoked` contains the default client (`marker == "default"`), not `session.built`. `save()` and `delete()` still call `self.objects.update`, `create`, or `delete` on a fresh manager.

`test_save_without_session_uses_the_default_client` already passes. Do not treat that pass as the task being done.

- [ ] **Step 3: Bind `save()` and `delete()`**

Replace `PrimaryBoto3Model.save` and `PrimaryBoto3Model.delete` with:

```python
def save(self, **kwargs):
    """
    Save the model through a manager bound to this model's session.

    A model with no session uses a default manager, because
    ``using(None)`` returns that manager unchanged.

    Keyword Args:
        kwargs: Arguments forwarded to the manager ``create`` or ``update``.

    Returns:
        The manager ``create`` or ``update`` result.

    Raises:
        NotUpdatableError: The model has a primary key and no ``update``.

    Side Effects:
        Calls AWS through the bound manager.

    """
    manager = self.objects.using(self.session)
    if self.pk:
        if hasattr(manager, "update"):
            return manager.update(self, **kwargs)
        msg = f"Model {self.__class__.__name__} is not updatable."
        raise NotUpdatableError(msg)
    return manager.create(self, **kwargs)

def delete(self):
    """
    Delete the model through a manager bound to this model's session.

    Returns:
        The manager ``delete`` result.

    Raises:
        ValueError: The model has no primary key.

    Side Effects:
        Calls AWS through the bound manager.

    """
    if not self.pk:
        msg = "Cannot delete a model that has not been saved."
        raise ValueError(msg)
    manager = self.objects.using(self.session)
    if isinstance(self.pk, OrderedDict):
        return manager.delete(**self.pk)
    return manager.delete(self.pk)
```

- [ ] **Step 4: Run the session tests**

Run: `.venv/bin/pytest tests/services/test_manager_session.py -v`

Expected: PASS, 8 tests.

- [ ] **Step 5: Commit**

```bash
git add tests/services/test_manager_session.py botocraft/services/abstract.py
git commit -m "$(cat <<'EOF'
BUGFIX: save and delete a model with the session stamped on it.

A model loaded through a bound manager otherwise wrote with the process
default client. Nested models are still unstamped; sessionize is unchanged.

EOF
)"
```

---

### Task 3: Security-group create uses the model session

**Files:**
- Modify: `tests/services/test_manager_session.py`
- Modify: `botocraft/mixins/ec2.py` (`SecurityGroupModelMixin.save`, the `self.objects.create` line near line 833)

- [ ] **Step 1: Add the failing test**

Append:

```python
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
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `.venv/bin/pytest tests/services/test_manager_session.py::test_security_group_create_uses_model_session -v`

Expected: FAIL. `log[0]` is `("create", None)` because `save()` calls `self.objects.create` on the unbound manager. The ingress entry is already `("ingress", session)`.

- [ ] **Step 3: Bind the create call**

In `SecurityGroupModelMixin.save`, replace:

```python
group_id = self.objects.create(self, **kwargs)
```

with:

```python
group_id = self.objects.using(self.session).create(self, **kwargs)
```

Leave the `authorize_ingress`, `get`, and `revoke_ingress` lines as they are. They already call `using(self.session)`.

- [ ] **Step 4: Run the test**

Run: `.venv/bin/pytest tests/services/test_manager_session.py -v`

Expected: PASS, 9 tests.

- [ ] **Step 5: Commit**

```bash
git add tests/services/test_manager_session.py botocraft/mixins/ec2.py
git commit -m "$(cat <<'EOF'
BUGFIX: create a security group with the session on the model.

The ingress calls already used using(session). The create call did not.

EOF
)"
```

---

### Task 4: DataSync helper keeps the bound manager

**Files:**
- Modify: `tests/services/test_manager_session.py`
- Modify: `botocraft/datasync.py` (`_bind_manager_session`, lines 109-130)

- [ ] **Step 1: Add the failing test**

Append:

```python
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
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `.venv/bin/pytest tests/services/test_manager_session.py::test_bind_manager_session_returns_the_bound_manager -v`

Expected: FAIL. `bound is manager` because the helper calls `using()` and then returns the original manager. `test_bind_manager_session_none_returns_the_same_manager` already passes.

- [ ] **Step 3: Return the bound manager**

Replace `_bind_manager_session` with:

```python
def _bind_manager_session(manager: Any, session: boto3.session.Session | None) -> Any:
    """
    Return a manager bound to ``session`` when one is supplied.

    Args:
        manager: Generated DataSync manager instance or compatible fake.
        session: Session to bind, if any.

    Returns:
        ``manager`` when ``session`` is ``None`` or ``manager`` has no
        ``using`` method. Otherwise the manager ``using(session)`` returns.

    """
    if session is None:
        return manager
    if hasattr(manager, "using"):
        return manager.using(session)
    manager.session = session
    return manager
```

The no-`using` branch still assigns `manager.session`. That branch is for fakes. Do not build a client there.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/pytest tests/services/test_manager_session.py -v`

Expected: PASS, 11 tests.

- [ ] **Step 5: Commit**

```bash
git add tests/services/test_manager_session.py botocraft/datasync.py
git commit -m "$(cat <<'EOF'
BUGFIX: keep the manager returned by using() in DataSync session binding.

The helper used to call using() for its side effect and return the original
manager. using() no longer mutates that manager.

EOF
)"
```

---

### Task 5: Document the contract

**Files:**
- Modify: `doc/source/overview/services.rst` (Sessions section, lines 89-109)
- Modify: `doc/source/overview/ses.rst` (lines 270-272)
- Modify: `doc/source/overview/kinesis.rst` (lines 33-35)

- [ ] **Step 1: Replace the Sessions section**

Replace the Sessions section in `doc/source/overview/services.rst`, from the `Sessions` heading through the `service = Service.objects.using(session).get(...)` example, with:

```rst
Sessions
^^^^^^^^

You may need to manage multiple AWS accounts and regions in the same codebase.
``botocraft`` provides a way to do this via sessions, which are simply
``boto3.session.Session`` objects bound to the proper account user or role.

``using(session)`` returns a new manager bound to that session. It does not
change the manager you called it on. Keep the returned manager and use it for
every call that must run with those credentials. ``using(None)`` returns the
same manager and does not rebind. One ``using()`` call does not affect any
other manager in the process.

The manager's methods call its client. The client on the manager returned by
``using(session)`` is built from that session.

A model returned by a bound manager carries that session on the top-level
model. ``save()`` and ``delete()`` on that model use it. Nested models are
not stamped. Their ``save()`` and ``delete()`` use a default manager.

Calling ``using(session)`` and then using the original manager does not raise.
Those later calls still use the original manager's client, usually the process
identity. Use the manager ``using()`` returns.

.. code-block:: python

    from botocraft.services import Service

    session = boto3.session.Session(
        aws_access_key_id='my-access-key',
        aws_secret_access_key='my-secret-key',
        region_name='us-west-2'
    )

    service = Service.objects.using(session).get('my-service', cluster='my-cluster')

    mgr = Service.objects.using(session)
    same = mgr.get('my-service', cluster='my-cluster')
    services = mgr.list()
```

The old example imported `Service` from `botocraft.models`. That package does not exist. This page already tells readers to import from `botocraft.services`.

Do not edit the `.. include:: _services_list.rst` line.

- [ ] **Step 2: Fix the two sticky sentences**

In `doc/source/overview/ses.rst`, replace:

```rst
If your application uses a non-default AWS session, call
``EmailIdentity.objects.using(session)`` before ``get`` or ``list``. General
session usage is covered in :doc:`/overview/services`.
```

with:

```rst
If your application uses a non-default AWS session, chain it:
``EmailIdentity.objects.using(session).get(...)`` or
``EmailIdentity.objects.using(session).list(...)``. General session usage is
covered in :doc:`/overview/services`.
```

In `doc/source/overview/kinesis.rst`, replace:

```rst
If you use a non-default AWS session, call
``KinesisStream.objects.using(session)`` before ``get`` or ``list``. General
session usage is covered in :doc:`/overview/services`.
```

with:

```rst
If you use a non-default AWS session, chain it:
``KinesisStream.objects.using(session).get(...)`` or
``KinesisStream.objects.using(session).list(...)``. General session usage is
covered in :doc:`/overview/services`.
```

Leave `doc/source/overview/cloudwatch.rst`, `cloudwatch_logs.rst`, and `bedrock.rst` unchanged. They already chain or point at `services.rst`.

- [ ] **Step 3: Commit**

```bash
git add doc/source/overview/services.rst doc/source/overview/ses.rst doc/source/overview/kinesis.rst
git commit -m "$(cat <<'EOF'
Document that using() returns a new manager and does not rebind the receiver.

Callers who ignore the return value still run with the original client.
Nested models do not inherit the session.

EOF
)"
```

---

### Task 6: Quality gate

**Files:**
- No planned edits. Fix only new failures from Tasks 1-5.

- [ ] **Step 1: Run the session tests**

Run: `.venv/bin/pytest tests/services/test_manager_session.py -v`

Expected: PASS, 11 tests.

- [ ] **Step 2: Lint and types**

Run:

```bash
.venv/bin/ruff check botocraft/services/abstract.py botocraft/datasync.py botocraft/mixins/ec2.py tests/services/test_manager_session.py
.venv/bin/mypy botocraft/services/abstract.py botocraft/datasync.py botocraft/mixins/ec2.py tests/services/test_manager_session.py
```

Expected: ruff reports no new errors. mypy reports no new errors in `abstract.py`, `datasync.py`, and the test file. If `botocraft/mixins/ec2.py` fails only on lines this change did not touch, record the errors and stop. Do not clean unrelated mixin errors.

- [ ] **Step 3: Docstring gate**

Run: `make napoleon-gate`

Expected: no new violations against the baseline. Do not edit the baseline file to silence a new violation. Fix the docstring instead.

- [ ] **Step 4: Update the knowledge graph**

Run: `graphify update .`

If `graphify-out/` has changes other than `graphify-out/cache/last_query_stamp`, commit them:

```bash
git add graphify-out
git commit -m "$(cat <<'EOF'
Update the knowledge graph after the session-bound manager change.

EOF
)"
```

- [ ] **Step 5: Stop before publish**

Do not bump the version. Do not push. Tell the maintainer the commits are ready and the public contract is the Sessions section plus the `using()` docstring.
