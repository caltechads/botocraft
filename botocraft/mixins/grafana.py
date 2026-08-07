"""
Handwritten helpers for the generated AWS Managed Grafana service managers.

AWS Managed Grafana automation in Botocraft is built on service account
tokens, not the legacy workspace API key operations
(``CreateWorkspaceApiKey`` / ``DeleteWorkspaceApiKey``).  Those operations
are intentionally not modeled anywhere in this module -- see
``docs/adr/0001-delete-previous-amg-service-account-token-during-rotation.md``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, cast

from botocraft.mixins.common import arg_value, coerce_queryset_results
from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.grafana import (
        ManagedGrafanaServiceAccount,
        ManagedGrafanaServiceAccountTokenWithKey,
        ManagedGrafanaWorkspace,
    )

# ----------
# Manager mixins
# ----------


class ManagedGrafanaWorkspaceManagerMixin:
    """
    Manager helpers for :py:class:`botocraft.services.grafana.ManagedGrafanaWorkspace`.

    AWS Managed Grafana's ``ListWorkspaces`` operation only returns the
    lightweight ``WorkspaceSummary`` shape, not the full
    ``WorkspaceDescription`` shape that the rest of this manager's methods
    return, so the generated CRUDL machinery cannot support a plain
    zero-argument ``list()``.  This mixin paginates ``list_workspaces`` and
    hydrates each result with ``describe_workspace`` so callers always get
    full :py:class:`ManagedGrafanaWorkspace` instances back.
    """

    #: Boto3 client used by the generated manager.
    client: Any

    def list(self) -> PrimaryBoto3ModelQuerySet:
        """
        Return all AWS Managed Grafana workspaces visible to the current
        session.

        Returns:
            A queryset of :py:class:`botocraft.services.grafana.ManagedGrafanaWorkspace`
            objects.

        """
        from botocraft.services.grafana import ManagedGrafanaWorkspace

        workspace_ids: list[str] = []
        paginator = self.client.get_paginator("list_workspaces")
        for page in paginator.paginate():
            for summary in page.get("workspaces", []):
                workspace_id = summary.get("id")
                if workspace_id:
                    workspace_ids.append(workspace_id)

        workspaces: list[ManagedGrafanaWorkspace] = []
        for workspace_id in workspace_ids:
            response = self.client.describe_workspace(workspaceId=workspace_id)
            workspaces.append(ManagedGrafanaWorkspace(**response["workspace"]))
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", workspaces))
        self.sessionize(query_set)  # type: ignore[attr-defined]
        return query_set


class ManagedGrafanaServiceAccountTokenManagerMixin:
    """
    Manager helpers for
    :py:class:`botocraft.services.grafana.ManagedGrafanaServiceAccountToken`.

    AWS Managed Grafana has no token-update operation, so Botocraft treats
    "rotate" -- create a replacement token, then delete the previous token
    id the caller supplies -- as the update workflow for service account
    tokens.  See
    ``docs/adr/0001-delete-previous-amg-service-account-token-during-rotation.md``.
    """

    #: Boto3 client used by the generated manager.
    client: Any

    def rotate(
        self,
        *,
        name: str,
        secondsToLive: int,  # noqa: N803
        serviceAccountId: str,  # noqa: N803
        workspaceId: str,  # noqa: N803
        previous_token_id: str,
    ) -> ManagedGrafanaServiceAccountTokenWithKey:
        """
        Rotate an AWS Managed Grafana service account token.

        This creates a replacement token, then deletes the previous token
        id the caller supplied.  If the delete fails, the exception from AWS
        propagates unchanged: the newly-created token remains in AWS, and
        Botocraft does not try to compensate for the partial success by
        returning the new token's key through a failure path.

        Args:
            previous_token_id: The id of the token to delete once the
                replacement token has been created.  Rotation deletes
                exactly this token id; it never guesses at "all other
                tokens" or "the oldest token".

        Keyword Args:
            name: The name to give the replacement token.
            secondsToLive: How long the replacement token should live, in
                seconds.
            serviceAccountId: The service account that owns both the
                previous and replacement tokens.
            workspaceId: The workspace that owns the service account.

        Raises:
            botocore.exceptions.ClientError: Deleting the previous token
                failed.  The replacement token has already been created in
                AWS and is not deleted by Botocraft in this failure path.

        Returns:
            The newly-created :py:class:`ManagedGrafanaServiceAccountTokenWithKey`,
            including its plaintext ``key``.  This is the only time that key
            is visible.

        """
        from botocraft.services.grafana import ManagedGrafanaServiceAccountToken

        # The generated ``create()`` method only reads ``name``,
        # ``serviceAccountId``, and ``workspaceId`` off this model when
        # building the ``CreateWorkspaceServiceAccountToken`` call -- ``id``,
        # ``createdAt``, and ``expiresAt`` are AWS-assigned output-only
        # fields that ``create()`` never reads from the model, so these are
        # inert placeholders that only exist to satisfy the model's required
        # fields.
        model = ManagedGrafanaServiceAccountToken(
            id="",
            name=name,
            createdAt=datetime.now(timezone.utc),
            expiresAt=datetime.now(timezone.utc),
            serviceAccountId=serviceAccountId,
            workspaceId=workspaceId,
        )
        replacement = self.create(model, secondsToLive)  # type: ignore[attr-defined]
        self.delete(  # type: ignore[attr-defined]
            tokenId=previous_token_id,
            serviceAccountId=serviceAccountId,
            workspaceId=workspaceId,
        )
        return replacement


# ----------
# Decorators
# ----------


def service_account_create_to_service_account(
    func: Callable[..., Any],
) -> Callable[..., ManagedGrafanaServiceAccount]:
    """
    Rebuild the flat ``CreateWorkspaceServiceAccount`` response into a proper
    :py:class:`ManagedGrafanaServiceAccount`.

    The boto3 response for ``create_workspace_service_account`` is a flat
    shape (``id``, ``name``, ``grafanaRole``, ``workspaceId``) that does not
    match the ``ServiceAccountSummary`` shape used everywhere else in this
    service, which has ``isDisabled`` instead of ``workspaceId``.  This
    decorator maps the flat response onto a real
    :py:class:`ManagedGrafanaServiceAccount` instance, defaulting
    ``isDisabled`` to ``"false"`` (a string, matching the botocore shape's
    ``isDisabled`` field type) since a newly-created service account is
    never disabled.

    Args:
        func: Generated manager method returning the raw flat create
            response.

    Returns:
        Wrapped manager method returning a public
        :py:class:`ManagedGrafanaServiceAccount`.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> ManagedGrafanaServiceAccount:
        from botocraft.services.grafana import ManagedGrafanaServiceAccount

        response = func(self, *args, **kwargs)
        payload = response.model_dump(exclude_none=True)
        service_account = ManagedGrafanaServiceAccount(
            id=payload.get("id"),
            name=payload.get("name"),
            grafanaRole=payload.get("grafanaRole"),
            workspaceId=payload.get("workspaceId"),
            isDisabled="false",
        )
        self.sessionize(service_account)
        return service_account

    return wrapper


def service_accounts_add_workspace_context(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Reattach the ``workspaceId`` scope to listed service accounts.

    ``ServiceAccountSummary`` items in a ``ListWorkspaceServiceAccounts``
    response don't carry ``workspaceId`` -- it's only present on the
    response envelope, alongside the summary list -- so this decorator
    copies the caller-supplied ``workspaceId`` onto each returned model.

    Args:
        func: Generated manager method returning service account summaries.

    Returns:
        Wrapped manager method returning a queryset of service accounts with
        ``workspaceId`` populated.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.grafana import ManagedGrafanaServiceAccount

        workspace_id = cast("str | None", arg_value(args, kwargs, "workspaceId", 0))
        results = func(self, *args, **kwargs)
        service_accounts = []
        for service_account in coerce_queryset_results(results):
            payload = service_account.model_dump(exclude_none=True, by_alias=True)
            payload["workspaceId"] = workspace_id
            service_accounts.append(ManagedGrafanaServiceAccount(**payload))
        query_set = PrimaryBoto3ModelQuerySet(
            cast("list[Boto3Model]", service_accounts)
        )
        self.sessionize(query_set)
        return query_set

    return wrapper


def service_account_token_create_to_token_with_key(
    func: Callable[..., Any],
) -> Callable[..., ManagedGrafanaServiceAccountTokenWithKey]:
    """
    Merge the ``CreateWorkspaceServiceAccountToken`` response into a
    :py:class:`ManagedGrafanaServiceAccountTokenWithKey`.

    The boto3 response nests ``id``, ``name``, and the plaintext ``key``
    under ``serviceAccountToken``, while ``serviceAccountId`` and
    ``workspaceId`` are flat siblings on the response envelope, not nested
    inside ``serviceAccountToken``.  This decorator merges both into a
    single model.

    Args:
        func: Generated manager method returning the raw nested create
            response.

    Returns:
        Wrapped manager method returning a public
        :py:class:`ManagedGrafanaServiceAccountTokenWithKey`, including its
        plaintext ``key``.

    """

    @wraps(func)
    def wrapper(
        self, *args: Any, **kwargs: Any
    ) -> ManagedGrafanaServiceAccountTokenWithKey:
        from botocraft.services.grafana import (
            ManagedGrafanaServiceAccountTokenWithKey,
        )

        response = func(self, *args, **kwargs)
        payload = response.model_dump(exclude_none=True)
        token_payload = payload.get("serviceAccountToken") or {}
        token = ManagedGrafanaServiceAccountTokenWithKey(
            id=token_payload.get("id"),
            name=token_payload.get("name"),
            key=token_payload.get("key"),
            serviceAccountId=payload.get("serviceAccountId"),
            workspaceId=payload.get("workspaceId"),
        )
        self.sessionize(token)
        return token

    return wrapper


def service_account_tokens_add_context(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Reattach the ``workspaceId``/``serviceAccountId`` scope to listed tokens.

    ``ServiceAccountTokenSummary`` items in a
    ``ListWorkspaceServiceAccountTokens`` response don't carry
    ``workspaceId`` or ``serviceAccountId`` -- those are only present on the
    response envelope, alongside the token list -- so this decorator copies
    the caller-supplied values onto each returned model.  This never
    involves the plaintext token key: ``ServiceAccountTokenSummary`` has no
    ``key`` field, and this decorator doesn't add one.

    Args:
        func: Generated manager method returning service account token
            summaries.

    Returns:
        Wrapped manager method returning a queryset of tokens with
        ``workspaceId``/``serviceAccountId`` populated.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.grafana import ManagedGrafanaServiceAccountToken

        # ``ListWorkspaceServiceAccountTokensRequest`` declares its required
        # members in this order: ``serviceAccountId``, then ``workspaceId``.
        # That is also the positional-argument order the generated ``list()``
        # method uses, so the fallback positions below must match it.
        service_account_id = cast(
            "str | None", arg_value(args, kwargs, "serviceAccountId", 0)
        )
        workspace_id = cast("str | None", arg_value(args, kwargs, "workspaceId", 1))
        results = func(self, *args, **kwargs)
        tokens = []
        for token in coerce_queryset_results(results):
            payload = token.model_dump(exclude_none=True, by_alias=True)
            payload["workspaceId"] = workspace_id
            payload["serviceAccountId"] = service_account_id
            tokens.append(ManagedGrafanaServiceAccountToken(**payload))
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", tokens))
        self.sessionize(query_set)
        return query_set

    return wrapper
