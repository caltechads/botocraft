# Changelog

## [0.36.0] - 2026-10-20

### Changed

- `using(session)` now returns a new manager bound to that session. The manager you called it on is left as it was. Keep the returned manager and use it for every call that must run with those credentials. `using(None)` still returns the same manager and does not rebind. One `using()` call does not affect any other manager in the process.
- Calling `using(session)` and then using the original manager does not raise an error. Those later calls still run with the original manager's client, usually the process identity. Code that depended on `using()` changing the manager in place must use the manager `using()` returns. There is no deprecation period.

### Fixed

- Fix shared managers picking up whichever session was bound last. A held manager could run a later call with another caller's credentials.
- Fix `save()` and `delete()` so a model loaded under a session writes and deletes with that session. Nested models are still not stamped with the session, and their `save()` and `delete()` use a default manager.
- Fix security group creation so the create call uses the session on the model. Authorizing ingress already did.
- Fix DataSync helpers so they keep the manager `using()` returns, instead of going back to the original manager and its client.
- Fix a manager bound to a new session so it recomputes cached values that came from the previous session, such as an account id.
