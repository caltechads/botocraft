# Return a Session-Bound Manager from using()

`Boto3ModelManager.using()` used to assign `session` and `client` on the
receiver and return that same object. The next call on that object used
whichever session landed last. `Model.objects` builds a new manager on every
access, so chained `Model.objects.using(session).get(...)` did not by itself
share a manager across callers. Any held manager did. That breaks per-request
assumed-role credentials when two threads share one manager.

`.using(session)` will return a new manager and will not modify the
receiver. That manager holds the same session object the caller passed, and
its client is `session.client(service_name)`. Manager methods call that
client. Copying the receiver and changing only `.session` is still the leak,
because a fresh `Boto3ModelManager` already has a `client` from
`boto3.client()` and a different `session` from `boto3.session.Session()`.
`.using(None)` returns the same manager and does not rebind. There is no
context manager, no lock, and no ambient context variable. `save()` and
`delete()` on a model call `self.objects.using(self.session)`. `set_session`
and `sessionize` stay as they are. `sessionize` stamps the top-level primary
or readonly-primary model and then returns, so nested models are not stamped.
Sticky mutation is removed in this release, with no deprecation window.

## Considered Options

- Make `.using()` a context manager that swaps the session for a block and
  then restores it.
- Return a new manager and also offer that context manager.
- Keep mutating the receiver, and tell callers to invoke `.using()` immediately
  before each call.
- Store the session in a `contextvar` so a bare `Model.objects.get()` picks up
  the current task's session.
- Warn for a release, then stop mutating the receiver.
- Make a discarded `.using()` fail loudly, so the old pattern cannot succeed
  with the wrong credentials.

We chose a new manager because chained call sites already use the return value.
A context manager would put the shared write back for the length of the block,
which is the race. An ambient context variable would make
`Model.objects.get()` depend on who last entered a scope. A deprecation window
would leave the race in place. A loud failure is not available: Python cannot
tell that the caller discarded the return value, and requiring a new parameter
on every manager method would break default-credential callers. The old
pattern stays silent. The leak this change closes is two callers sharing one
manager.

## Consequences

- Callers who called `.using(session)` and then used the original manager must
  keep the manager `.using()` returns. Chained
  `Model.objects.using(session).get(...)` stays valid. The old pattern does not
  raise. `mgr.using(session)` followed by `mgr.get()` still calls AWS, with
  the receiver's existing client, which is usually the process identity.
- Two threads may share a manager. Each `shared.using(session)` returns a
  distinct manager whose client was built from that thread's session. A call
  on one does not change the other, or the shared receiver. The concurrency
  test must assert the client that was invoked, not only `manager.session`.
- `sessionize` stamps the top-level primary or readonly-primary model and
  stops. Nested models keep `session is None`. Their `save()` and `delete()`
  use a default manager. The credential guarantee is the top-level model
  returned by the bound manager, not every object in the response.
- `save()` and `delete()` on that top-level model call
  `self.objects.using(self.session)`, including overrides such as
  security-group `save()`. A hand-built model whose `session` is `None` still
  uses a default manager, because `.using(None)` returns that manager
  unchanged. Tests must cover `save()` and `delete()`, not only `.using()`.
- `datasync._bind_manager_session` must return the manager `.using()` returns.
  Other in-repo call sites already use the return value.
- The contract is written in the handwritten Sessions section of
  `doc/source/overview/services.rst` and on the `using()` docstring, which the
  generated API pages render. `overview/ses.rst` and `overview/kinesis.rst`
  must show the chained call. Generated files under `doc/source/api/services/`
  are not edited, and `botocraft.sync` does not change.
- The change is handwritten in `botocraft/services/abstract.py`. Tests must
  show that one `.using()` does not affect the receiver or a manager already
  bound to another session, that two threads calling `.using()` on one shared
  manager each invoke their own client, and that `save()` and `delete()` on a
  stamped model use that model's session.
- The release note goes in the commit message. This repository does not keep a
  changelog file. The version bump is done by the maintainer with
  `bumpversion`.
