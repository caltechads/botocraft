from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Any, Protocol, cast

import botocore.exceptions
import botocore.model
import botocore.session
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, create_model

#: CloudTrail ``eventSource`` values needing explicit botocore service ids.
EVENT_SOURCE_SERVICE_ALIASES: dict[str, str] = {
    "email.amazonaws.com": "ses",
    "monitoring.amazonaws.com": "cloudwatch",
    "execute-api.amazonaws.com": "apigateway",
}


class CloudTrailApiCallDetailProtocol(Protocol):
    """
    Structural type for CloudTrail API-call detail payloads on EventBridge events.
    """

    #: CloudTrail service endpoint, such as ``acm.amazonaws.com``.
    eventSource: str
    #: CloudTrail API operation name, such as ``RequestCertificate``.
    eventName: str
    #: Request payload recorded by CloudTrail for the API operation.
    requestParameters: dict[str, Any] | None


class CloudTrailApiCallMixin:
    """
    Lazy, botocore-backed parsing helpers for CloudTrail API-call EventBridge events.

    Event instances keep raw ``requestParameters`` on ``detail``. Call
    :meth:`parsed_request` when you want a best-effort view aligned with the AWS API
    operation named by ``detail.eventName``.
    """

    #: CloudTrail detail payload on the EventBridge event.
    detail: CloudTrailApiCallDetailProtocol

    def parsed_request_model(self, *, strict: bool = False) -> type[BaseModel] | None:
        """
        Return a cached Pydantic model for this event's CloudTrail request parameters.

        The model is built from the matching botocore operation input shape for
        ``detail.eventSource`` and ``detail.eventName``. Returns ``None`` when the
        service or operation cannot be resolved.

        Keyword Args:
            strict: When ``True``, mark botocore-required input members as required
                on the generated model. When ``False``, all members are optional so
                partial or redacted CloudTrail payloads still validate.

        Returns:
            Generated request model type, or ``None`` when no botocore operation
            matches the event.

        """
        service_name = service_name_from_event_source(self.detail.eventSource)
        if service_name is None:
            return None
        return request_model_for_operation(
            service_name,
            self.detail.eventName,
            strict=strict,
        )

    def parsed_request(
        self, *, strict: bool = False
    ) -> BaseModel | dict[str, Any]:
        """
        Parse ``detail.requestParameters`` against the botocore operation input shape.

        Keyword Args:
            strict: Forwarded to :meth:`parsed_request_model`.

        Returns:
            A validated Pydantic model when botocore resolution succeeds, otherwise
            the raw ``requestParameters`` mapping (or an empty dict when absent).

        """
        parameters = self.detail.requestParameters
        if parameters is None:
            return {}
        model_cls = self.parsed_request_model(strict=strict)
        if model_cls is None:
            return parameters
        return model_cls.model_validate(parameters)


def service_name_from_event_source(event_source: str) -> str | None:
    """
    Resolve a botocore service name from a CloudTrail ``eventSource`` value.

    Args:
        event_source: CloudTrail endpoint value, such as ``acm.amazonaws.com``.

    Returns:
        Botocore service id when recognized, otherwise ``None``.

    """
    if event_source in EVENT_SOURCE_SERVICE_ALIASES:
        return EVENT_SOURCE_SERVICE_ALIASES[event_source]
    if event_source.endswith(".amazonaws.com"):
        return event_source.removesuffix(".amazonaws.com")
    return None


@lru_cache(maxsize=1)
def _botocore_session() -> botocore.session.Session:
    """
    Return the shared botocore session used for CloudTrail shape resolution.

    Returns:
        Cached botocore session.

    """
    return botocore.session.get_session()


def _cloudtrail_field_alias(member_name: str) -> str | AliasChoices:
    """
    Build validation aliases that accept CloudTrail camelCase and botocore PascalCase.

    Args:
        member_name: Botocore structure member name.

    Returns:
        Alias configuration for the generated Pydantic field.

    """
    if not member_name:
        return member_name
    cloudtrail_name = member_name[0].lower() + member_name[1:]
    if cloudtrail_name == member_name:
        return member_name
    return AliasChoices(member_name, cloudtrail_name)


class _CloudTrailShapeModelBuilder:
    """
    Build cached Pydantic models from botocore shapes for CloudTrail request parsing.
    """

    def __init__(self) -> None:
        """
        Initialize an empty generated-model cache for CloudTrail shape conversion.
        """
        #: Cache of generated models keyed by service, shape name, and strictness.
        self._models: dict[tuple[str, str, bool], type[BaseModel]] = {}

    def build_model(
        self,
        service_name: str,
        shape: botocore.model.Shape,
        *,
        strict: bool,
        model_name: str,
    ) -> type[BaseModel]:
        """
        Convert a botocore shape into a Pydantic model, reusing cached nested models.

        Args:
            service_name: Botocore service id used for nested shape caching.
            shape: Botocore shape to convert.
            strict: Whether botocore-required members are required on the model.

        Keyword Args:
            model_name: Name assigned to the generated top-level model.

        Returns:
            Generated Pydantic model class.

        """
        cache_key = (service_name, shape.name, strict)
        cached = self._models.get(cache_key)
        if cached is not None:
            return cached
        if shape.type_name == "structure":
            model = self._build_structure_model(
                service_name,
                cast("botocore.model.StructureShape", shape),
                strict=strict,
                model_name=model_name,
            )
        else:
            annotation = self._annotation_for_shape(service_name, shape, strict=strict)
            model = create_model(
                model_name,
                __config__=ConfigDict(extra="ignore"),
                value=(annotation, ...),
            )
        self._models[cache_key] = model
        return model

    def _build_structure_model(
        self,
        service_name: str,
        shape: botocore.model.StructureShape,
        *,
        strict: bool,
        model_name: str,
    ) -> type[BaseModel]:
        """
        Create a Pydantic model for a botocore structure shape.

        Args:
            service_name: Botocore service id used for nested shape caching.
            shape: Structure shape to convert.
            strict: Whether botocore-required members are required on the model.

        Keyword Args:
            model_name: Name assigned to the generated model.

        Returns:
            Generated Pydantic model class.

        """
        field_definitions: dict[str, Any] = {}
        for member_name, member_shape in shape.members.items():
            annotation = self._annotation_for_shape(
                service_name,
                member_shape,
                strict=strict,
            )
            is_required = strict and member_name in shape.required_members
            if is_required:
                field_definitions[member_name] = (
                    annotation,
                    Field(validation_alias=_cloudtrail_field_alias(member_name)),
                )
            else:
                field_definitions[member_name] = (
                    annotation | None,
                    Field(
                        default=None,
                        validation_alias=_cloudtrail_field_alias(member_name),
                    ),
                )
        return create_model(
            model_name,
            __config__=ConfigDict(extra="ignore", populate_by_name=True),
            **field_definitions,
        )

    def _annotation_for_shape(
        self,
        service_name: str,
        shape: botocore.model.Shape,
        *,
        strict: bool,
    ) -> Any:
        """
        Map a botocore shape to a Python type used in generated Pydantic models.

        Args:
            service_name: Botocore service id used for nested shape caching.
            shape: Botocore shape to convert.

        Keyword Args:
            strict: Whether nested required members are enforced.

        Returns:
            Type annotation for the shape.

        """
        type_name = shape.type_name
        annotation: Any
        if type_name == "string":
            annotation = str
        elif type_name == "boolean":
            annotation = bool
        elif type_name in {"integer", "long"}:
            annotation = int
        elif type_name in {"float", "double"}:
            annotation = float
        elif type_name == "timestamp":
            annotation = datetime
        elif type_name == "blob":
            annotation = bytes
        elif type_name == "list":
            list_shape = cast("botocore.model.ListShape", shape)
            member_type = self._annotation_for_shape(
                service_name,
                list_shape.member,
                strict=strict,
            )
            annotation = list[member_type]  # type: ignore[valid-type]
        elif type_name == "map":
            map_shape = cast("botocore.model.MapShape", shape)
            value_type = self._annotation_for_shape(
                service_name,
                map_shape.value,
                strict=strict,
            )
            key_type = self._annotation_for_shape(
                service_name,
                map_shape.key,
                strict=strict,
            )
            annotation = dict[key_type, value_type]  # type: ignore[valid-type]
        elif type_name == "structure":
            annotation = self.build_model(
                service_name,
                shape,
                strict=strict,
                model_name=shape.name,
            )
        else:
            annotation = Any
        return annotation


#: Shared builder reused across CloudTrail request-model resolution.
_SHAPE_MODEL_BUILDER = _CloudTrailShapeModelBuilder()


@lru_cache(maxsize=256)
def request_model_for_operation(
    service_name: str,
    event_name: str,
    strict: bool = False,
) -> type[BaseModel] | None:
    """
    Build or fetch a cached Pydantic model for a botocore operation input shape.

    Args:
        service_name: Botocore service id, such as ``acm``.
        event_name: CloudTrail API operation name, such as ``RequestCertificate``.

    Keyword Args:
        strict: When ``True``, required botocore input members are required fields.

    Returns:
        Generated model type, or ``None`` when the service or operation is unknown.

    """
    try:
        service_model = _botocore_session().get_service_model(service_name)
        operation = service_model.operation_model(event_name)
    except (
        botocore.exceptions.UnknownServiceError,
        botocore.model.OperationNotFoundError,
    ):
        return None
    input_shape = operation.input_shape
    if input_shape is None:
        return None
    return _SHAPE_MODEL_BUILDER.build_model(
        service_name,
        input_shape,
        strict=strict,
        model_name=f"CloudTrail_{service_name}_{event_name}_Request",
    )
