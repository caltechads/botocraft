"""Handwritten helpers for generated classic SES service managers."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Protocol, cast

from botocraft.mixins.common import arg_value, coerce_queryset_results
from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.ses import (
        SESBulkEmailDestinationStatus,
        SESConfigurationSet,
        SESCustomVerificationEmailTemplate,
        SESIdentity,
        SESReceiptFilter,
        SESReceiptRuleSet,
        SESTemplate,
    )


class _SESManagerProtocol(Protocol):
    """Protocol for generated managers used by handwritten SES mixins."""

    #: Generated boto3 client bound to the current SES manager instance.
    client: Any

    def get(self, *args: Any, **kwargs: Any) -> Any:
        """
        Return a model from the manager.

        Args:
            *args: Positional arguments forwarded to the manager lookup.

        Keyword Args:
            **kwargs: Keyword arguments forwarded to the manager lookup.

        Returns:
            Manager-specific model or response object.

        """

    def serialize(self, value: Any) -> Any:
        """
        Serialize one value for boto3.

        Args:
            value: Python value to serialize for boto3.

        Returns:
            Serialized value suitable for boto3 request payloads.

        """

    def sessionize(self, model: Any) -> None:
        """
        Attach active session to one model or queryset.

        Args:
            model: Model or queryset that should inherit manager session state.

        Side Effects:
            Mutates the supplied object graph to attach active session state.

        """


def _infer_identity_type(identity: str) -> str:
    """
    Infer whether an SES identity is an email address or domain.

    Args:
        identity: SES identity string returned by AWS.

    Returns:
        ``EmailAddress`` when the identity looks like an email address,
        otherwise ``Domain``.

    """
    return "EmailAddress" if "@" in identity else "Domain"


class SESConfigurationSetManagerMixin:
    """
    Handwritten mutation methods for classic SES configuration sets.
    """

    def get(
        self: _SESManagerProtocol,
        name: str,
        *,
        configuration_set_attribute_names: list[str] | None = None,
    ) -> SESConfigurationSet | None:
        """
        Load one configuration set from raw SES describe payload.

        Args:
            name: Configuration set name to load.

        Keyword Args:
            configuration_set_attribute_names: Optional SES attribute names to
                request.

        Returns:
            Public configuration set model, or ``None`` when response absent.

        """
        from botocraft.services.ses import SESConfigurationSet

        args: dict[str, Any] = {
            "ConfigurationSetName": self.serialize(name),
            "ConfigurationSetAttributeNames": self.serialize(
                configuration_set_attribute_names
            ),
        }
        response = self.client.describe_configuration_set(
            **{key: value for key, value in args.items() if value is not None}
        )
        payload = cast("dict[str, Any]", response.get("ConfigurationSet", {}))
        payload["EventDestinations"] = [
            {
                **item,
                "EventDestinationName": item.get("Name"),
            }
            for item in cast(
                "list[dict[str, Any]]",
                response.get("EventDestinations", []),
            )
        ]
        payload["TrackingOptions"] = response.get("TrackingOptions")
        payload["DeliveryOptions"] = response.get("DeliveryOptions")
        payload["ReputationOptions"] = response.get("ReputationOptions")
        model = SESConfigurationSet(**payload)
        self.sessionize(model)
        return cast("SESConfigurationSet", model)

    def create(
        self: _SESManagerProtocol,
        model: SESConfigurationSet,
    ) -> SESConfigurationSet | None:
        """
        Create a configuration set, then return refreshed public model.

        Args:
            model: Public configuration set model to create.

        Returns:
            Refreshed configuration set model, or ``None`` when lookup fails.

        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        payload = {"Name": data.get("Name", data.get("ConfigurationSetName"))}
        self.client.create_configuration_set(ConfigurationSet=self.serialize(payload))
        return self.get(name=model.ConfigurationSetName)


class SESTemplateManagerMixin:
    """
    Handwritten mutation and render methods for classic SES templates.
    """

    def create(self: _SESManagerProtocol, model: SESTemplate) -> SESTemplate | None:
        """
        Create an SES template, then return refreshed public model.

        Args:
            model: Public template model to create.

        Returns:
            Refreshed template model, or ``None`` when lookup fails.

        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        payload = {
            key: value
            for key, value in data.items()
            if key in {"TemplateName", "SubjectPart", "TextPart", "HtmlPart"}
        }
        self.client.create_template(Template=self.serialize(payload))
        return self.get(name=model.TemplateName)

    def update(self: _SESManagerProtocol, model: SESTemplate) -> SESTemplate | None:
        """
        Update an SES template, then return refreshed public model.

        Args:
            model: Public template model to update.

        Returns:
            Refreshed template model, or ``None`` when lookup fails.

        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        payload = {
            key: value
            for key, value in data.items()
            if key in {"TemplateName", "SubjectPart", "TextPart", "HtmlPart"}
        }
        self.client.update_template(Template=self.serialize(payload))
        return self.get(name=model.TemplateName)

    def render(self: _SESManagerProtocol, name: str, template_data: str) -> str:
        """
        Render an SES template with replacement data.

        Args:
            name: Template name to render.
            template_data: JSON replacement data accepted by SES.

        Returns:
            Rendered MIME content preview from SES.

        """
        response = self.client.test_render_template(
            TemplateName=self.serialize(name),
            TemplateData=self.serialize(template_data),
        )
        return cast("str", response["RenderedTemplate"])

    def send_mail(  # noqa: PLR0913
        self: _SESManagerProtocol,
        Source: str,  # noqa: N803
        Destination: Any,  # noqa: N803
        Template: str,  # noqa: N803
        TemplateData: str,  # noqa: N803
        *,
        ReplyToAddresses: list[str] | None = None,  # noqa: N803
        ReturnPath: str | None = None,  # noqa: N803
        SourceArn: str | None = None,  # noqa: N803
        ReturnPathArn: str | None = None,  # noqa: N803
        Tags: list[Any] | None = None,  # noqa: N803
        ConfigurationSetName: str | None = None,  # noqa: N803
    ) -> str:
        """
        Send a templated email using a classic SES template.

        Args:
            Source: Verified sender identity.
            Destination: Destination payload accepted by SES.
            Template: Template name to send.
            TemplateData: JSON replacement data accepted by SES.

        Keyword Args:
            ReplyToAddresses: Reply-to email addresses.
            ReturnPath: Bounce address for the message.
            SourceArn: ARN used for sending authorization.
            ReturnPathArn: ARN used for return-path authorization.
            Tags: SES message tags to attach to the send.
            ConfigurationSetName: Optional configuration set name.

        Returns:
            AWS SES message identifier.

        """
        response = self.client.send_templated_email(
            **{
                key: value
                for key, value in {
                    "Source": self.serialize(Source),
                    "Destination": self.serialize(Destination),
                    "Template": self.serialize(Template),
                    "TemplateData": self.serialize(TemplateData),
                    "ReplyToAddresses": self.serialize(ReplyToAddresses),
                    "ReturnPath": self.serialize(ReturnPath),
                    "SourceArn": self.serialize(SourceArn),
                    "ReturnPathArn": self.serialize(ReturnPathArn),
                    "Tags": self.serialize(Tags),
                    "ConfigurationSetName": self.serialize(ConfigurationSetName),
                }.items()
                if value is not None
            }
        )
        return cast("str", response["MessageId"])

    def send_bulk_templated_mail(  # noqa: PLR0913
        self: _SESManagerProtocol,
        Source: str,  # noqa: N803
        Template: str,  # noqa: N803
        Destinations: list[Any],  # noqa: N803
        *,
        SourceArn: str | None = None,  # noqa: N803
        ReplyToAddresses: list[str] | None = None,  # noqa: N803
        ReturnPath: str | None = None,  # noqa: N803
        ReturnPathArn: str | None = None,  # noqa: N803
        ConfigurationSetName: str | None = None,  # noqa: N803
        DefaultTags: list[Any] | None = None,  # noqa: N803
        DefaultTemplateData: str | None = None,  # noqa: N803
    ) -> list[SESBulkEmailDestinationStatus]:
        """
        Send bulk templated email using a classic SES template.

        Args:
            Source: Verified sender identity.
            Template: Template name to send.
            Destinations: Bulk destination payloads accepted by SES.

        Keyword Args:
            SourceArn: ARN used for sending authorization.
            ReplyToAddresses: Reply-to email addresses.
            ReturnPath: Bounce address for the message.
            ReturnPathArn: ARN used for return-path authorization.
            ConfigurationSetName: Optional configuration set name.
            DefaultTags: Default SES message tags to attach to each send.
            DefaultTemplateData: Default JSON replacement data for destinations.

        Returns:
            Per-destination send statuses from AWS SES.

        """
        from botocraft.services.ses import SESBulkEmailDestinationStatus

        response = self.client.send_bulk_templated_email(
            **{
                key: value
                for key, value in {
                    "Source": self.serialize(Source),
                    "Template": self.serialize(Template),
                    "Destinations": self.serialize(Destinations),
                    "SourceArn": self.serialize(SourceArn),
                    "ReplyToAddresses": self.serialize(ReplyToAddresses),
                    "ReturnPath": self.serialize(ReturnPath),
                    "ReturnPathArn": self.serialize(ReturnPathArn),
                    "ConfigurationSetName": self.serialize(ConfigurationSetName),
                    "DefaultTags": self.serialize(DefaultTags),
                    "DefaultTemplateData": self.serialize(DefaultTemplateData),
                }.items()
                if value is not None
            }
        )
        results = [
            SESBulkEmailDestinationStatus(**status)
            for status in cast("list[dict[str, Any]]", response.get("Status", []))
        ]
        self.sessionize(results)
        return cast("list[SESBulkEmailDestinationStatus]", results)


class SESCustomVerificationEmailTemplateManagerMixin:
    """
    Handwritten send method for SES custom verification email templates.
    """

    def send_verification_mail(
        self: _SESManagerProtocol,
        EmailAddress: str,  # noqa: N803
        TemplateName: str,  # noqa: N803
        *,
        ConfigurationSetName: str | None = None,  # noqa: N803
    ) -> str:
        """
        Send a custom verification email using one SES verification template.

        Args:
            EmailAddress: Recipient email address to verify.
            TemplateName: Custom verification template name to use.

        Keyword Args:
            ConfigurationSetName: Optional configuration set name.

        Returns:
            AWS SES message identifier.

        """
        response = self.client.send_custom_verification_email(
            **{
                key: value
                for key, value in {
                    "EmailAddress": self.serialize(EmailAddress),
                    "TemplateName": self.serialize(TemplateName),
                    "ConfigurationSetName": self.serialize(ConfigurationSetName),
                }.items()
                if value is not None
            }
        )
        return cast("str", response["MessageId"])


class SESIdentityManagerMixin:
    """
    Handwritten sender identity methods for classic SES identities.
    """

    def get(self: _SESManagerProtocol, identity: str) -> SESIdentity | None:
        """
        Load one SES sender identity from verification attributes.

        Args:
            identity: Email address or domain identity to load.

        Returns:
            Public sender identity model, or ``None`` when absent.

        """
        from botocraft.services.ses import SESIdentity

        response = self.client.get_identity_verification_attributes(
            Identities=self.serialize([identity])
        )
        attributes = cast(
            "dict[str, dict[str, Any]]",
            response.get("VerificationAttributes", {}),
        )
        payload = dict(attributes.get(identity, {}))
        if not payload:
            return None
        payload["Identity"] = identity
        payload["IdentityType"] = _infer_identity_type(identity)
        model = SESIdentity(**payload)
        self.sessionize(model)
        return cast("SESIdentity", model)

    def create(self: _SESManagerProtocol, model: SESIdentity) -> SESIdentity | None:
        """
        Verify an SES sender identity, then return refreshed public model.

        Args:
            model: Public sender identity model to verify.

        Returns:
            Refreshed sender identity model, or ``None`` when lookup fails.

        """
        token: str | None = None
        if model.Identity is None:
            msg = "Unable to verify SES identity without an Identity value."
            raise ValueError(msg)
        identity_type = model.IdentityType or _infer_identity_type(model.Identity)
        if identity_type == "EmailAddress":
            self.client.verify_email_identity(EmailAddress=self.serialize(model.Identity))
        else:
            response = self.client.verify_domain_identity(
                Domain=self.serialize(model.Identity)
            )
            token = cast("str | None", response.get("VerificationToken"))
        refreshed = cast("SESIdentity | None", self.get(model.Identity))
        if refreshed is not None and token is not None:
            refreshed.VerificationToken = token
        return refreshed

    def send_mail(  # noqa: PLR0913
        self: _SESManagerProtocol,
        Source: str,  # noqa: N803
        Destination: Any,  # noqa: N803
        Message: Any,  # noqa: N803
        *,
        ReplyToAddresses: list[str] | None = None,  # noqa: N803
        ReturnPath: str | None = None,  # noqa: N803
        SourceArn: str | None = None,  # noqa: N803
        ReturnPathArn: str | None = None,  # noqa: N803
        Tags: list[Any] | None = None,  # noqa: N803
        ConfigurationSetName: str | None = None,  # noqa: N803
    ) -> str:
        """
        Send a classic SES email from one verified identity.

        Args:
            Source: Verified sender identity.
            Destination: Destination payload accepted by SES.
            Message: Message payload accepted by SES.

        Keyword Args:
            ReplyToAddresses: Reply-to email addresses.
            ReturnPath: Bounce address for the message.
            SourceArn: ARN used for sending authorization.
            ReturnPathArn: ARN used for return-path authorization.
            Tags: SES message tags to attach to the send.
            ConfigurationSetName: Optional configuration set name.

        Returns:
            AWS SES message identifier.

        """
        response = self.client.send_email(
            **{
                key: value
                for key, value in {
                    "Source": self.serialize(Source),
                    "Destination": self.serialize(Destination),
                    "Message": self.serialize(Message),
                    "ReplyToAddresses": self.serialize(ReplyToAddresses),
                    "ReturnPath": self.serialize(ReturnPath),
                    "SourceArn": self.serialize(SourceArn),
                    "ReturnPathArn": self.serialize(ReturnPathArn),
                    "Tags": self.serialize(Tags),
                    "ConfigurationSetName": self.serialize(ConfigurationSetName),
                }.items()
                if value is not None
            }
        )
        return cast("str", response["MessageId"])

    def send_raw_mail(  # noqa: PLR0913
        self: _SESManagerProtocol,
        Source: str,  # noqa: N803
        RawMessage: Any,  # noqa: N803
        *,
        Destinations: list[str] | None = None,  # noqa: N803
        FromArn: str | None = None,  # noqa: N803
        SourceArn: str | None = None,  # noqa: N803
        ReturnPathArn: str | None = None,  # noqa: N803
        Tags: list[Any] | None = None,  # noqa: N803
        ConfigurationSetName: str | None = None,  # noqa: N803
    ) -> str:
        """
        Send a raw classic SES email from one verified identity.

        Args:
            Source: Verified sender identity.
            RawMessage: Raw MIME payload accepted by SES.

        Keyword Args:
            Destinations: Optional recipient email addresses.
            FromArn: ARN used for from-address authorization.
            SourceArn: ARN used for source authorization.
            ReturnPathArn: ARN used for return-path authorization.
            Tags: SES message tags to attach to the send.
            ConfigurationSetName: Optional configuration set name.

        Returns:
            AWS SES message identifier.

        """
        response = self.client.send_raw_email(
            **{
                key: value
                for key, value in {
                    "Source": self.serialize(Source),
                    "RawMessage": self.serialize(RawMessage),
                    "Destinations": self.serialize(Destinations),
                    "FromArn": self.serialize(FromArn),
                    "SourceArn": self.serialize(SourceArn),
                    "ReturnPathArn": self.serialize(ReturnPathArn),
                    "Tags": self.serialize(Tags),
                    "ConfigurationSetName": self.serialize(ConfigurationSetName),
                }.items()
                if value is not None
            }
        )
        return cast("str", response["MessageId"])


class SESReceiptFilterManagerMixin:
    """
    Handwritten mutation methods for SES receipt filters.
    """

    def create(self: _SESManagerProtocol, model: SESReceiptFilter) -> None:
        """
        Create a receipt filter from public model data.

        Args:
            model: Public receipt filter model to create.

        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        payload = {
            "Name": data.get("Name", data.get("FilterName")),
            "IpFilter": data.get("IpFilter"),
        }
        self.client.create_receipt_filter(Filter=self.serialize(payload))


class SESReceiptRuleSetManagerMixin:
    """
    Handwritten mutation methods for SES receipt rule sets.
    """

    def get(self: _SESManagerProtocol, name: str) -> SESReceiptRuleSet | None:
        """
        Load one receipt rule set from raw SES describe payload.

        Args:
            name: Receipt rule set name to load.

        Returns:
            Public receipt rule set model, or ``None`` when response absent.

        """
        from botocraft.services.ses import SESReceiptRuleSet

        response = self.client.describe_receipt_rule_set(
            RuleSetName=self.serialize(name)
        )
        payload = cast("dict[str, Any]", response.get("Metadata", {}))
        payload["Rules"] = [
            {
                **item,
                "ReceiptRuleName": item.get("Name"),
            }
            for item in cast("list[dict[str, Any]]", response.get("Rules", []))
        ]
        model = SESReceiptRuleSet(**payload)
        self.sessionize(model)
        return cast("SESReceiptRuleSet", model)

    def create(
        self: _SESManagerProtocol,
        model: SESReceiptRuleSet,
    ) -> SESReceiptRuleSet | None:
        """
        Create an empty receipt rule set, then return refreshed public model.

        Args:
            model: Public receipt rule set model to create.

        Returns:
            Refreshed receipt rule set model, or ``None`` when lookup fails.

        """
        self.client.create_receipt_rule_set(
            RuleSetName=self.serialize(model.ReceiptRuleSetName)
        )
        return self.get(name=model.ReceiptRuleSetName)


class SESResponseHelper:
    """
    Hydrate classic SES manager responses into stable public models.

    Args:
        manager: Generated manager instance that owns boto3 client and session.

    """

    #: Generated manager instance used for follow-up AWS calls and sessionization.
    manager: Any

    def __init__(self, manager: Any) -> None:
        """
        Initialize helper for one generated manager call.

        Args:
            manager: Generated manager instance that owns boto3 client and session.

        """
        #: Generated manager instance used for follow-up AWS calls and sessionization.
        self.manager = manager

    def _payload(self, response: Any) -> dict[str, Any]:
        """
        Convert a generated response object or dict into payload data.

        Args:
            response: Generated response wrapper, model, or plain dictionary.

        Returns:
            Dictionary payload for follow-up shaping.

        """
        if response is None:
            return {}
        if hasattr(response, "model_dump"):
            return cast("dict[str, Any]", response.model_dump(exclude_none=True))
        if isinstance(response, dict):
            return dict(response)
        return cast("dict[str, Any]", dict(vars(response)))

    def _sessionize(self, model: Any) -> Any:
        """
        Attach active boto3 session to one model or queryset.

        Args:
            model: Model or queryset to sessionize.

        Returns:
            Same object after sessionization.

        Side Effects:
            Binds manager session to returned object graph.

        """
        self.manager.sessionize(model)
        return model

    def _refresh_by_name(self, name: str) -> Any:
        """
        Refresh a resource by calling generated ``get(name=...)`` method.

        Args:
            name: Identifier accepted by the generated ``get`` method.

        Returns:
            Refreshed model instance, or ``None`` when lookup fails.

        """
        return self.manager.get(name=name)

    def refresh_from_model_attr(
        self,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        *,
        model_attr: str,
    ) -> Any:
        """
        Refresh resource after mutation using identifier stored on model argument.

        Args:
            args: Positional decorator arguments.
            kwargs: Keyword decorator arguments.

        Keyword Args:
            model_attr: Attribute to read from first model argument.

        Raises:
            ValueError: Resource identifier was missing from mutation model.

        Returns:
            Refreshed model instance.

        """
        model = arg_value(args, kwargs, "model", 0)
        name = getattr(model, model_attr, None)
        if name is None:
            msg = f"Unable to refresh SES model without '{model_attr}'."
            raise ValueError(msg)
        return self._refresh_by_name(cast("str", name))

    def template_metadata_models(
        self,
        results: Any,
    ) -> PrimaryBoto3ModelQuerySet:
        """
        Convert template metadata summaries into public template models.

        Args:
            results: List or queryset of template metadata objects.

        Returns:
            Queryset of public template models.

        """
        from botocraft.services.ses import SESTemplate

        templates: list[SESTemplate] = []
        for item in coerce_queryset_results(results):
            payload = self._payload(item)
            if "TemplateName" not in payload and "Name" in payload:
                payload["TemplateName"] = payload.pop("Name")
            templates.append(SESTemplate(**payload))
        queryset = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", templates))
        return cast("PrimaryBoto3ModelQuerySet", self._sessionize(queryset))

    def identity_models(self, results: Any) -> PrimaryBoto3ModelQuerySet:
        """
        Convert SES identity strings into public sender identity models.

        Args:
            results: List or queryset of identity strings.

        Returns:
            Queryset of public sender identity models.

        """
        from botocraft.services.ses import SESIdentity

        identities = [
            SESIdentity(
                Identity=identity,
                IdentityType=_infer_identity_type(identity),
            )
            for identity in coerce_queryset_results(results)
        ]
        queryset = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", identities))
        return cast("PrimaryBoto3ModelQuerySet", self._sessionize(queryset))

    def custom_verification_template_from_response(
        self,
        response: Any,
        *args: Any,
        **kwargs: Any,
    ) -> SESCustomVerificationEmailTemplate | None:
        """
        Convert get-custom-verification-template response into public model.

        Args:
            response: Generated response object from
                ``get_custom_verification_email_template``.
            *args: Positional arguments from wrapped manager call.

        Keyword Args:
            **kwargs: Keyword arguments from wrapped manager call.

        Returns:
            Public custom verification email template model, or ``None`` when
            response absent.

        """
        from botocraft.services.ses import SESCustomVerificationEmailTemplate

        payload = self._payload(response)
        if not payload:
            return None
        if payload.get("TemplateName") is None:
            requested = arg_value(args, kwargs, "name", 0)
            if requested is not None:
                payload["TemplateName"] = requested
        model = SESCustomVerificationEmailTemplate(**payload)
        return cast("SESCustomVerificationEmailTemplate", self._sessionize(model))


def template_metadata_to_models(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Convert list-template metadata into public template models.

    Args:
        func: Generated ``list`` method returning template metadata.

    Returns:
        Wrapped ``list`` method returning public template models.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        helper = SESResponseHelper(self)
        return helper.template_metadata_models(func(self, *args, **kwargs))

    return wrapper


def identity_names_to_models(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Convert SES identity strings into public sender identity models.

    Args:
        func: Generated ``list`` method returning identity strings.

    Returns:
        Wrapped ``list`` method returning public sender identity models.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        helper = SESResponseHelper(self)
        return helper.identity_models(func(self, *args, **kwargs))

    return wrapper


def custom_verification_template_response_to_model(
    func: Callable[..., Any],
) -> Callable[..., SESCustomVerificationEmailTemplate | None]:
    """
    Convert get-custom-verification-template response into public model.

    Args:
        func: Generated ``get`` method returning wrapper response.

    Returns:
        Wrapped getter returning public custom verification email template.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        helper = SESResponseHelper(self)
        return helper.custom_verification_template_from_response(
            func(self, *args, **kwargs),
            *args,
            **kwargs,
        )

    return wrapper


def refresh_custom_verification_template_after_mutation(
    func: Callable[..., Any],
) -> Callable[..., SESCustomVerificationEmailTemplate | None]:
    """
    Refresh a custom verification email template after mutation.

    Args:
        func: Generated mutation method.

    Returns:
        Wrapped mutation returning refreshed custom verification template.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        helper = SESResponseHelper(self)
        func(self, *args, **kwargs)
        return helper.refresh_from_model_attr(
            args,
            kwargs,
            model_attr="TemplateName",
        )

    return wrapper
