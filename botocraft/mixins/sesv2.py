"""Handwritten helpers for generated SESv2 service managers."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, cast

from botocraft.mixins.common import arg_value, coerce_queryset_results
from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.sesv2 import (
        ConfigurationSet,
        DedicatedIpPool,
        DeliverabilityTestReport,
        EmailIdentity,
        MultiRegionEndpoint,
        Tenant,
    )


def _as_payload(value: Any) -> dict[str, Any]:
    """
    Normalize a botocraft model or boto-style mapping into a plain dict.

    Args:
        value: Mapping-like or model-like object to normalize.

    Returns:
        Plain dictionary representation.

    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return cast("dict[str, Any]", value.model_dump(exclude_none=True))
    return cast("dict[str, Any]", dict(value))


def _sessionize(self: Any, value: Any) -> Any:
    """
    Attach manager session state to returned models or querysets.

    Args:
        self: Generated manager instance.
        value: Model or queryset to bind.

    Returns:
        Same value after session binding.

    """
    self.sessionize(value)
    return value


def _refresh_model(
    self: Any,
    *,
    getter_kw: str,
    identifier: Any,
) -> Any:
    """
    Re-fetch a model using the generated manager ``get`` method.

    Args:
        self: Generated manager instance.

    Keyword Args:
        getter_kw: Keyword argument name accepted by ``get``.
        identifier: Identifier value to pass back into ``get``.

    Returns:
        Refreshed model instance.

    """
    return self.get(**{getter_kw: identifier})


def _refresh_from_model_attr(
    self: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    *,
    model_attr: str,
    getter_kw: str,
) -> Any:
    """
    Refresh a resource after mutation using identifier on model argument.

    Args:
        self: Generated manager instance.
        args: Positional decorator arguments.
        kwargs: Keyword decorator arguments.

    Keyword Args:
        model_attr: Attribute to read from the first model argument.
        getter_kw: Keyword name accepted by ``get``.

    Raises:
        ValueError: Resource identifier was missing from the mutation model.

    Returns:
        Refreshed model instance.

    """
    model = arg_value(args, kwargs, "model", 0)
    identifier = getattr(model, model_attr, None)
    if identifier is None:
        msg = f"Unable to refresh SESv2 model without '{model_attr}'."
        raise ValueError(msg)
    return _refresh_model(self, getter_kw=getter_kw, identifier=identifier)


def configuration_set_names_to_models(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate configuration set names into full public models.

    Args:
        func: Generated ``list`` method returning configuration set names.

    Returns:
        Wrapped ``list`` method returning hydrated models.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.sesv2 import ConfigurationSet

        raw = func(self, *args, **kwargs)
        names = [item for item in coerce_queryset_results(raw) if isinstance(item, str)]
        models = [
            ConfigurationSet(**self.client.get_configuration_set(ConfigurationSetName=name))
            for name in names
        ]
        queryset = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", models))
        return _sessionize(self, queryset)

    return wrapper


def refresh_configuration_set_after_mutation(
    func: Callable[..., Any],
) -> Callable[..., ConfigurationSet]:
    """
    Refresh a configuration set after create-style mutations.

    Args:
        func: Generated mutation method.

    Returns:
        Wrapped mutation returning refreshed configuration set.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        func(self, *args, **kwargs)
        return _refresh_from_model_attr(
            self,
            args,
            kwargs,
            model_attr="ConfigurationSetName",
            getter_kw="ConfigurationSetName",
        )

    return wrapper


def email_identity_response_to_model(
    func: Callable[..., Any],
) -> Callable[..., EmailIdentity]:
    """
    Convert ``get_email_identity`` responses into public identity models.

    Args:
        func: Generated ``get`` method returning get-response payload.

    Returns:
        Wrapped getter returning :class:`EmailIdentity`.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.sesv2 import EmailIdentity

        payload = _as_payload(func(self, *args, **kwargs))
        payload["EmailIdentity"] = arg_value(args, kwargs, "identity", 0)
        model = EmailIdentity(**payload)
        return _sessionize(self, model)

    return wrapper


def email_identity_summaries_to_models(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Convert list-email-identity summaries into public identity models.

    Args:
        func: Generated ``list`` method returning identity summaries.

    Returns:
        Wrapped ``list`` method returning public identity models.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.sesv2 import EmailIdentity

        raw = func(self, *args, **kwargs)
        models: list[EmailIdentity] = []
        for item in coerce_queryset_results(raw):
            payload = _as_payload(item)
            payload["EmailIdentity"] = payload.pop("IdentityName", None)
            models.append(EmailIdentity(**payload))
        queryset = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", models))
        return _sessionize(self, queryset)

    return wrapper


def refresh_email_identity_after_mutation(
    func: Callable[..., Any],
) -> Callable[..., EmailIdentity]:
    """
    Refresh an email identity after create mutations.

    Args:
        func: Generated mutation method.

    Returns:
        Wrapped mutation returning refreshed email identity.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        func(self, *args, **kwargs)
        return _refresh_from_model_attr(
            self,
            args,
            kwargs,
            model_attr="EmailIdentity",
            getter_kw="EmailIdentity",
        )

    return wrapper


def refresh_contact_list_after_mutation(
    func: Callable[..., Any],
) -> Callable[..., Any]:
    """
    Refresh a contact list after create or update mutations.

    Args:
        func: Generated mutation method.

    Returns:
        Wrapped mutation returning refreshed contact list.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        func(self, *args, **kwargs)
        return _refresh_from_model_attr(
            self,
            args,
            kwargs,
            model_attr="ContactListName",
            getter_kw="ContactListName",
        )

    return wrapper


def refresh_email_template_after_mutation(
    func: Callable[..., Any],
) -> Callable[..., Any]:
    """
    Refresh an email template after create or update mutations.

    Args:
        func: Generated mutation method.

    Returns:
        Wrapped mutation returning refreshed email template.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        func(self, *args, **kwargs)
        return _refresh_from_model_attr(
            self,
            args,
            kwargs,
            model_attr="TemplateName",
            getter_kw="TemplateName",
        )

    return wrapper


def refresh_suppressed_destination_after_mutation(
    func: Callable[..., Any],
) -> Callable[..., Any]:
    """
    Refresh a suppressed destination after upsert mutations.

    Args:
        func: Generated mutation method.

    Returns:
        Wrapped mutation returning refreshed suppressed destination.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        func(self, *args, **kwargs)
        return _refresh_from_model_attr(
            self,
            args,
            kwargs,
            model_attr="EmailAddress",
            getter_kw="EmailAddress",
        )

    return wrapper


def deliverability_test_report_response_to_model(
    func: Callable[..., Any],
) -> Callable[..., DeliverabilityTestReport]:
    """
    Flatten deliverability test report responses into public models.

    Args:
        func: Generated ``get`` method returning wrapper payload.

    Returns:
        Wrapped getter returning flattened deliverability report model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.sesv2 import DeliverabilityTestReport

        payload = _as_payload(func(self, *args, **kwargs))
        report_payload = _as_payload(
            payload.pop("DeliverabilityTestReportInstance", None)
        )
        merged = {**report_payload, **payload}
        model = DeliverabilityTestReport(**merged)
        return _sessionize(self, model)

    return wrapper


def refresh_deliverability_test_report_after_create(
    func: Callable[..., Any],
) -> Callable[..., DeliverabilityTestReport]:
    """
    Refresh a deliverability test report after creation.

    Args:
        func: Generated create method.

    Returns:
        Wrapped create returning refreshed report.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        response = _as_payload(func(self, *args, **kwargs))
        report_id = response.get("ReportId")
        if report_id is None:
            msg = "Unable to refresh SESv2 deliverability report without ReportId."
            raise ValueError(msg)
        return _refresh_model(self, getter_kw="ReportId", identifier=report_id)

    return wrapper


def multi_region_endpoint_response_to_model(
    func: Callable[..., Any],
) -> Callable[..., MultiRegionEndpoint]:
    """
    Convert multi-region endpoint responses into public models.

    Args:
        func: Generated ``get`` method returning wrapper payload.

    Returns:
        Wrapped getter returning public endpoint model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.sesv2 import MultiRegionEndpoint

        model = MultiRegionEndpoint(**_as_payload(func(self, *args, **kwargs)))
        return _sessionize(self, model)

    return wrapper


def refresh_multi_region_endpoint_after_mutation(
    func: Callable[..., Any],
) -> Callable[..., MultiRegionEndpoint]:
    """
    Refresh a multi-region endpoint after create mutations.

    Args:
        func: Generated mutation method.

    Returns:
        Wrapped mutation returning refreshed endpoint.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        func(self, *args, **kwargs)
        return _refresh_from_model_attr(
            self,
            args,
            kwargs,
            model_attr="EndpointName",
            getter_kw="EndpointName",
        )

    return wrapper


def tenant_response_to_model(
    func: Callable[..., Any],
) -> Callable[..., Tenant]:
    """
    Convert create-tenant responses into public tenant models.

    Args:
        func: Generated create method returning top-level tenant payload.

    Returns:
        Wrapped create method returning tenant model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.sesv2 import Tenant

        model = Tenant(**_as_payload(func(self, *args, **kwargs)))
        return _sessionize(self, model)

    return wrapper


def dedicated_ip_pool_names_to_models(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate dedicated IP pool names into full public models.

    Args:
        func: Generated ``list`` method returning pool names.

    Returns:
        Wrapped ``list`` method returning hydrated pool models.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.sesv2 import DedicatedIpPool

        raw = func(self, *args, **kwargs)
        names = [item for item in coerce_queryset_results(raw) if isinstance(item, str)]
        models: list[DedicatedIpPool] = []
        for name in names:
            response = self.client.get_dedicated_ip_pool(PoolName=name)
            payload = _as_payload(response.get("DedicatedIpPool"))
            models.append(DedicatedIpPool(**payload))
        queryset = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", models))
        return _sessionize(self, queryset)

    return wrapper


def refresh_dedicated_ip_pool_after_mutation(
    func: Callable[..., Any],
) -> Callable[..., DedicatedIpPool]:
    """
    Refresh a dedicated IP pool after create or update mutations.

    Args:
        func: Generated mutation method.

    Returns:
        Wrapped mutation returning refreshed pool.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        func(self, *args, **kwargs)
        return _refresh_from_model_attr(
            self,
            args,
            kwargs,
            model_attr="PoolName",
            getter_kw="PoolName",
        )

    return wrapper


class SESV2EmailIdentityManagerMixin:
    """
    Handwritten SESv2 email identity manager methods.

    The generated manager cannot represent the identity name cleanly because the list
    shape uses ``IdentityName`` while get/create identify resources through the
    ``EmailIdentity`` request parameter. This mixin keeps the public Botocraft model on
    ``EmailIdentity`` and hides the shape mismatch.
    """

    #: Generated boto3 client attached by the manager base class.
    client: Any

    def create(
        self,
        model: Any,
        DkimSigningAttributes: Any | None = None,  # noqa: N803
    ) -> EmailIdentity:
        """
        Create an email identity and return the refreshed public model.

        Args:
            model: Email identity model containing the identity name and optional
                configuration-set and tag inputs.

        Keyword Args:
            DkimSigningAttributes: Optional BYODKIM or Easy DKIM signing settings.

        Returns:
            Refreshed public email identity model.

        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        email_identity = data.get("IdentityName") or model.EmailIdentity
        args = {
            "EmailIdentity": email_identity,
            "Tags": data.get("Tags"),
            "DkimSigningAttributes": self.serialize(DkimSigningAttributes),  # type: ignore[attr-defined]
            "ConfigurationSetName": data.get("ConfigurationSetName"),
        }
        self.client.create_email_identity(  # type: ignore[attr-defined]
            **{key: value for key, value in args.items() if value is not None}
        )
        created = self.get(cast("str", args["EmailIdentity"]))
        if created is None:
            msg = "Unable to refresh SESv2 email identity after creation."
            raise ValueError(msg)
        return created

    def get(self, identity: str) -> EmailIdentity | None:
        """
        Get one email identity by email address or domain.

        Args:
            identity: Email address or domain identity name.

        Returns:
            Public email identity model when found.

        """
        from botocraft.services.sesv2 import EmailIdentity

        response = self.client.get_email_identity(  # type: ignore[attr-defined]
            EmailIdentity=self.serialize(identity),  # type: ignore[attr-defined]
        )
        payload = _as_payload(response)
        payload["IdentityName"] = identity
        model = EmailIdentity(**payload)
        return cast("EmailIdentity", _sessionize(self, model))

    def list(
        self,
        *,
        NextToken: str | None = None,  # noqa: N803
        PageSize: int | None = None,  # noqa: N803
    ) -> PrimaryBoto3ModelQuerySet:
        """
        List all email identities associated with the current account.

        Keyword Args:
            NextToken: Optional pagination token.
            PageSize: Optional page size.

        Returns:
            Queryset of public email identity models.

        """
        from botocraft.services.sesv2 import EmailIdentity

        response = self.client.list_email_identities(  # type: ignore[attr-defined]
            **{
                key: value
                for key, value in {
                    "NextToken": self.serialize(NextToken),  # type: ignore[attr-defined]
                    "PageSize": self.serialize(PageSize),  # type: ignore[attr-defined]
                }.items()
                if value is not None
            }
        )
        models: list[EmailIdentity] = []
        for item in response.get("EmailIdentities", []):
            payload = _as_payload(item)
            models.append(EmailIdentity(**payload))
        queryset = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", models))
        return cast("PrimaryBoto3ModelQuerySet", _sessionize(self, queryset))

    def delete(self, identity: str) -> None:
        """
        Delete one email identity by email address or domain.

        Args:
            identity: Email address or domain identity name.

        Side Effects:
            Deletes the SESv2 identity from AWS when it exists.

        """
        self.client.delete_email_identity(  # type: ignore[attr-defined]
            EmailIdentity=self.serialize(identity),  # type: ignore[attr-defined]
        )


class SESV2DeliverabilityTestReportManagerMixin:
    """
    Handwritten SESv2 deliverability report manager methods.

    Get responses wrap the actual report in a nested ``DeliverabilityTestReport``
    object plus placement statistics. This mixin flattens that structure into the
    public Botocraft model and refreshes create operations using the returned report
    identifier.
    """

    #: Generated boto3 client attached by the manager base class.
    client: Any

    def create(self, model: Any) -> DeliverabilityTestReport:
        """
        Create a deliverability test report and return the refreshed public model.

        Args:
            model: Deliverability test request model containing sender and content.

        Returns:
            Refreshed deliverability test report model.

        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        response = self.client.create_deliverability_test_report(  # type: ignore[attr-defined]
            **{
                key: value
                for key, value in {
                    "FromEmailAddress": data.get("FromEmailAddress"),
                    "Content": data.get("Content"),
                    "ReportName": data.get("ReportName"),
                    "Tags": data.get("Tags"),
                }.items()
                if value is not None
            }
        )
        report_id = response.get("ReportId")
        if report_id is None:
            msg = "Unable to refresh SESv2 deliverability report without ReportId."
            raise ValueError(msg)
        created = self.get(cast("str", report_id))
        if created is None:
            msg = "Unable to refresh SESv2 deliverability report after creation."
            raise ValueError(msg)
        return created

    def get(self, ReportId: str) -> DeliverabilityTestReport | None:  # noqa: N803
        """
        Get one deliverability test report by report identifier.

        Args:
            ReportId: Unique predictive inbox placement report identifier.

        Returns:
            Flattened public deliverability test report model when found.

        """
        from botocraft.services.sesv2 import DeliverabilityTestReport

        response = self.client.get_deliverability_test_report(  # type: ignore[attr-defined]
            ReportId=self.serialize(ReportId),  # type: ignore[attr-defined]
        )
        report_payload = _as_payload(response.get("DeliverabilityTestReport"))
        merged = {
            **report_payload,
            "OverallPlacement": response.get("OverallPlacement"),
            "IspPlacements": response.get("IspPlacements"),
            "Message": response.get("Message"),
            "Tags": response.get("Tags"),
        }
        model = DeliverabilityTestReport(**merged)
        return cast("DeliverabilityTestReport", _sessionize(self, model))
