# ruff: noqa: N803, PLR0913
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Iterable,
    Iterator,
    Literal,
    TypeVar,
    cast,
)

from pydantic_core import core_schema

if TYPE_CHECKING:
    from datetime import datetime

    from boto3.session import Session
    from botocore.eventstream import EventStream
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema

    from botocraft.services.bedrock import Guardrail
    from botocraft.services.bedrock_runtime import (
        AsyncInvokeOutputDataConfig,
        BedrockMessage,
        Conversation,
        ConversationManager,
        ConverseStreamOutput,
        ConverseStreamResponse,
        CountTokensInput,
        Document,
        GetAsyncInvokeResponse,
        GuardrailApplication,
        GuardrailApplicationManager,
        GuardrailConfiguration,
        GuardrailContentBlock,
        GuardrailStreamConfiguration,
        InferenceConfiguration,
        InvokeModelResponse,
        InvokeModelWithResponseStreamResponse,
        ListAsyncInvokesResponse,
        ModelInputPayload,
        OutputConfig,
        PerformanceConfiguration,
        PromptVariableValues,
        ResponseStream,
        ServiceTier,
        StartAsyncInvokeResponse,
        SystemContentBlock,
        TokenCount,
        ToolConfiguration,
    )

#: Generic typed event yielded by Bedrock stream adapters.
TEvent = TypeVar("TEvent")


def _guardrail_identifier_and_version(
    guardrail: Guardrail | str,
    guardrail_version: str | None = None,
) -> tuple[str, str]:
    """
    Resolve runtime guardrail inputs into identifier and version strings.

    Args:
        guardrail: Guardrail object or raw guardrail identifier.
        guardrail_version: Explicit version override for the guardrail.

    Raises:
        ValueError: Guardrail version is missing.

    Returns:
        Guardrail identifier and version.

    """
    if isinstance(guardrail, str):
        guardrail_identifier = guardrail
    else:
        guardrail_identifier = cast("str", guardrail.guardrailId)
        if guardrail_version is None:
            guardrail_version = guardrail.version
    if guardrail_version is None:
        msg = "guardrailVersion is required when guardrail has no version."
        raise ValueError(msg)
    return guardrail_identifier, guardrail_version


class BedrockEventStream(Generic[TEvent]):
    """
    Lazy adapter around boto3 Bedrock Runtime event streams.

    Args:
        source: Raw boto3 event stream, generic iterable of raw Bedrock event
            dictionaries, single raw event dictionary, or existing typed event.

    """

    #: Raw stream source yielded by boto3 or tests.
    _source: EventStream | Iterable[Any] | dict[str, Any] | TEvent | None = None

    def __init__(
        self,
        source: EventStream | Iterable[Any] | dict[str, Any] | TEvent,
    ) -> None:
        """
        Store raw Bedrock stream source for lazy iteration.

        Args:
            source: Raw stream source yielded by boto3 or tests.

        """
        #: Raw stream source yielded by boto3 or tests.
        self._source = source

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """
        Build pydantic schema that coerces raw Bedrock streams into wrappers.

        Args:
            _source_type: Source type pydantic is building a schema for.
            _handler: Pydantic schema handler for nested schemas.

        Returns:
            Pydantic core schema for this wrapper type.

        """
        return core_schema.no_info_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, value: Any) -> BedrockEventStream[Any]:
        """
        Coerce pydantic field input into stream wrapper instance.

        Args:
            value: Raw value assigned to stream wrapper field.

        Returns:
            Stream wrapper instance.

        """
        if isinstance(value, cls):
            return value
        return cls(value)

    @classmethod
    def _event_model_type(cls) -> type[TEvent]:
        """
        Return concrete typed event model for this Bedrock stream wrapper.

        Raises:
            NotImplementedError: Subclass does not provide event model type.

        Returns:
            Event model class.

        """
        msg = f"{cls.__name__} must define _event_model_type()."
        raise NotImplementedError(msg)

    def _iter_source(self) -> Iterator[Any]:
        """
        Normalize raw stream source into iterator of raw Bedrock events.

        Returns:
            Iterator of raw event payloads.

        """
        from botocraft.services.abstract import Boto3Model

        if isinstance(self._source, dict | Boto3Model):
            yield self._source
            return
        yield from cast("Iterable[Any]", self._source)

    def _coerce_event(self, event: Any) -> TEvent:
        """
        Convert raw Bedrock event payload into typed event model.

        Args:
            event: Raw Bedrock event payload.

        Returns:
            Typed event model.

        """
        event_model = self._event_model_type()
        if isinstance(event, event_model):
            return event
        if isinstance(event, dict):
            return event_model(**event)
        msg = (
            f"{self.__class__.__name__} expected dict or {event_model.__name__} "
            f"event, got {type(event).__name__}."
        )
        raise TypeError(msg)

    def __iter__(self) -> Iterator[TEvent]:
        """
        Yield typed Bedrock stream events lazily.

        Yields:
            Typed Bedrock Runtime event objects.

        """
        for event in self._iter_source():
            yield self._coerce_event(event)

    def close(self) -> None:
        """
        Close underlying raw Bedrock stream when supported.

        Side Effects:
            Closes underlying boto3 event stream body when it exposes
            ``close()``.

        """
        close = getattr(self._source, "close", None)
        if callable(close):
            close()


class ConverseStream(BedrockEventStream["ConverseStreamOutput"]):
    """
    Typed iterator for ``converse_stream`` events.

    Args:
        source: Raw Bedrock Converse event stream source.

    """

    @classmethod
    def _event_model_type(cls) -> type[ConverseStreamOutput]:
        """
        Return typed event model for converse streaming.

        Returns:
            ``ConverseStreamOutput`` model class.

        """
        from botocraft.services.bedrock_runtime import ConverseStreamOutput

        return ConverseStreamOutput


class InvokeModelResponseStream(BedrockEventStream["ResponseStream"]):
    """
    Typed iterator for ``invoke_model_with_response_stream`` events.

    Args:
        source: Raw Bedrock invoke response stream source.

    """

    @classmethod
    def _event_model_type(cls) -> type[ResponseStream]:
        """
        Return typed event model for raw invoke streaming.

        Returns:
            ``ResponseStream`` model class.

        """
        from botocraft.services.bedrock_runtime import ResponseStream

        return ResponseStream


class ConverseStreamResponseMixin:
    """
    Iterable helpers for Bedrock Converse streaming responses.

    Args:
        No constructor arguments. This mixin expects ``stream`` attribute on
        response model.

    """

    def __iter__(self) -> Iterator[ConverseStreamOutput]:
        """
        Iterate typed Bedrock Converse events from response wrapper.

        Yields:
            Typed converse stream events.

        """
        stream = getattr(self, "stream", None)
        if stream is None:
            return
        yield from stream

    def close(self) -> None:
        """
        Close underlying Bedrock Converse stream if present.

        Side Effects:
            Closes underlying boto3 event stream when response contains one.

        """
        stream = getattr(self, "stream", None)
        if stream is not None:
            stream.close()


class InvokeModelWithResponseStreamResponseMixin:
    """
    Iterable helpers for raw Bedrock invoke streaming responses.

    Args:
        No constructor arguments. This mixin expects ``body`` attribute on
        response model.

    """

    def __iter__(self) -> Iterator[ResponseStream]:
        """
        Iterate typed raw invoke stream events from response wrapper.

        Yields:
            Typed raw invoke stream events.

        """
        body = getattr(self, "body", None)
        if body is None:
            return
        yield from body

    def close(self) -> None:
        """
        Close underlying raw invoke stream if present.

        Side Effects:
            Closes underlying boto3 event stream when response contains one.

        """
        body = getattr(self, "body", None)
        if body is not None:
            body.close()


class ConversationManagerMixin:
    """
    Extra handwritten Bedrock Runtime manager behavior.

    Args:
        No constructor arguments. This mixin expects a manager with a boto3
        ``client`` attribute.

    """

    def close(self) -> None:
        """
        Close underlying boto3 client resources.

        Side Effects:
            Closes HTTP resources held by the Bedrock Runtime boto3 client.

        """
        self.client.close()  # type: ignore[attr-defined]


class FoundationModelRuntimeMixin:
    """
    Convenience Bedrock Runtime helpers for foundation model instances.

    This mixin keeps human-facing API model-bound while delegating actual
    runtime calls to generated `bedrock-runtime` managers.
    """

    #: Boto3 session attached by Botocraft model managers.
    session: Session | None
    #: Runtime model identifier used for model-bound operations.
    modelId: str | None
    #: Runtime model ARN used for async invocation scoping.
    modelArn: str | None

    def _require_model_arn(self) -> str:
        """
        Return foundation model ARN for model-scoped async helpers.

        Raises:
            ValueError: Foundation model has no ``modelArn`` value.

        Returns:
            Foundation model ARN.

        """
        model_arn = getattr(self, "modelArn", None)
        if model_arn is None:
            msg = "FoundationModel.modelArn is required"
            raise ValueError(msg)
        return cast("str", model_arn)

    def close(self) -> None:
        """
        Close underlying Bedrock Runtime client resources for this model helper.

        Side Effects:
            Closes client resources held by a temporary ConversationManager.

        """
        from botocraft.services.bedrock_runtime import ConversationManager

        manager = cast("ConversationManager", ConversationManager().using(self.session))
        manager.close()

    def converse(
        self,
        messages: list[BedrockMessage] | None = None,
        *,
        system: list[SystemContentBlock] | None = None,
        guardrail: Guardrail | None = None,
        guardrailConfig: GuardrailConfiguration | None = None,
        toolConfig: ToolConfiguration | None = None,
        inferenceConfig: InferenceConfiguration | None = None,
        additionalModelRequestFields: Document | None = None,
        promptVariables: dict[str, PromptVariableValues] | None = None,
        additionalModelResponseFieldPaths: list[str] | None = None,
        requestMetadata: dict[str, str] | None = None,
        performanceConfig: PerformanceConfiguration | None = None,
        serviceTier: ServiceTier | None = None,
        outputConfig: OutputConfig | None = None,
    ) -> Conversation:
        """
        Run Bedrock Converse against this foundation model.

        Args:
            messages: Converse message payload.

        Keyword Args:
            system: Optional system prompt content.
            guardrail: Guardrail object to convert into runtime guardrail configuration.
            guardrailConfig: Explicit Bedrock Runtime guardrail configuration.
            toolConfig: Optional Bedrock tool configuration.
            inferenceConfig: Optional inference configuration.
            additionalModelRequestFields: Provider-specific request fields.
            promptVariables: Prompt variable values.
            additionalModelResponseFieldPaths: Extra provider response
                fields to include.
            requestMetadata: Optional request metadata.
            performanceConfig: Optional performance configuration.
            serviceTier: Optional Bedrock service tier.
            outputConfig: Optional output configuration.

        Raises:
            ValueError: `guardrail` and `guardrailConfig` are both provided.
            ValueError: Guardrail object has no version.

        Returns:
            Conversation response.

        """
        from botocraft.services.bedrock_runtime import ConversationManager

        if guardrail is not None and guardrailConfig is not None:
            msg = "guardrail and guardrailConfig cannot both be provided."
            raise ValueError(msg)
        guardrail_config: GuardrailConfiguration | None
        if guardrail is not None:
            guardrail_identifier, guardrail_version = _guardrail_identifier_and_version(
                guardrail
            )
            guardrail_config = cast(
                "GuardrailConfiguration",
                {
                    "guardrailIdentifier": guardrail_identifier,
                    "guardrailVersion": guardrail_version,
                },
            )
        else:
            guardrail_config = guardrailConfig
        manager = cast("ConversationManager", ConversationManager().using(self.session))
        return cast(
            "Conversation",
            manager.converse(
                cast("str", self.modelId),
                messages=messages,
                system=system,
                toolConfig=toolConfig,
                inferenceConfig=inferenceConfig,
                guardrailConfig=guardrail_config,
                additionalModelRequestFields=additionalModelRequestFields,
                promptVariables=promptVariables,
                additionalModelResponseFieldPaths=additionalModelResponseFieldPaths,
                requestMetadata=requestMetadata,
                performanceConfig=performanceConfig,
                serviceTier=serviceTier,
                outputConfig=outputConfig,
            ),
        )

    def converse_stream(
        self,
        messages: list[BedrockMessage] | None = None,
        *,
        system: list[SystemContentBlock] | None = None,
        guardrail: Guardrail | None = None,
        guardrailConfig: GuardrailStreamConfiguration | None = None,
        toolConfig: ToolConfiguration | None = None,
        inferenceConfig: InferenceConfiguration | None = None,
        additionalModelRequestFields: Document | None = None,
        promptVariables: dict[str, PromptVariableValues] | None = None,
        additionalModelResponseFieldPaths: list[str] | None = None,
        requestMetadata: dict[str, str] | None = None,
        performanceConfig: PerformanceConfiguration | None = None,
        serviceTier: ServiceTier | None = None,
        outputConfig: OutputConfig | None = None,
    ) -> ConverseStreamResponse:
        """
        Run streaming Bedrock Converse against this foundation model.

        Args:
            messages: Converse stream message payload.

        Keyword Args:
            system: Optional system prompt content.
            guardrail: Guardrail object to convert into runtime guardrail configuration.
            guardrailConfig: Explicit Bedrock Runtime guardrail stream configuration.
            toolConfig: Optional Bedrock tool configuration.
            inferenceConfig: Optional inference configuration.
            additionalModelRequestFields: Provider-specific request fields.
            promptVariables: Prompt variable values.
            additionalModelResponseFieldPaths: Extra provider response
                fields to include.
            requestMetadata: Optional request metadata.
            performanceConfig: Optional performance configuration.
            serviceTier: Optional Bedrock service tier.
            outputConfig: Optional output configuration.

        Raises:
            ValueError: `guardrail` and `guardrailConfig` are both provided.
            ValueError: Guardrail object has no version.

        Returns:
            Iterable streaming conversation response.

        """
        from botocraft.services.bedrock_runtime import ConversationManager

        if guardrail is not None and guardrailConfig is not None:
            msg = "guardrail and guardrailConfig cannot both be provided."
            raise ValueError(msg)
        guardrail_config: GuardrailStreamConfiguration | None
        if guardrail is not None:
            guardrail_identifier, guardrail_version = _guardrail_identifier_and_version(
                guardrail
            )
            guardrail_config = cast(
                "GuardrailStreamConfiguration",
                {
                    "guardrailIdentifier": guardrail_identifier,
                    "guardrailVersion": guardrail_version,
                },
            )
        else:
            guardrail_config = guardrailConfig
        manager = cast("ConversationManager", ConversationManager().using(self.session))
        return cast(
            "ConverseStreamResponse",
            manager.converse_stream(
                cast("str", self.modelId),
                messages=messages,
                system=system,
                toolConfig=toolConfig,
                inferenceConfig=inferenceConfig,
                guardrailConfig=guardrail_config,
                additionalModelRequestFields=additionalModelRequestFields,
                promptVariables=promptVariables,
                additionalModelResponseFieldPaths=additionalModelResponseFieldPaths,
                requestMetadata=requestMetadata,
                performanceConfig=performanceConfig,
                serviceTier=serviceTier,
                outputConfig=outputConfig,
            ),
        )

    def count_tokens(
        self,
        input: CountTokensInput,  # noqa: A002
    ) -> TokenCount:
        """
        Count tokens for runtime input against this foundation model.

        Args:
            input: Bedrock Runtime `CountTokens` input payload.

        Returns:
            Token count response.

        """
        from botocraft.services.bedrock_runtime import ConversationManager

        manager = cast("ConversationManager", ConversationManager().using(self.session))
        return cast(
            "TokenCount",
            manager.count_tokens(cast("str", self.modelId), input=input),
        )

    def invoke_model(
        self,
        body: bytes,
        contentType: str,
        *,
        accept: str | None = None,
        trace: Literal["ENABLED", "DISABLED", "ENABLED_FULL"] | None = None,
        guardrailIdentifier: str | None = None,
        guardrailVersion: str | None = None,
        performanceConfigLatency: Literal["standard", "optimized"] | None = None,
        serviceTier: Literal["priority", "default", "flex", "reserved"] | None = None,
    ) -> InvokeModelResponse:
        """
        Invoke this foundation model with raw Bedrock Runtime request payload.

        Args:
            body: Input body for model inference.
            contentType: MIME type of input body.

        Keyword Args:
            accept: Desired MIME type for response body.
            trace: Optional trace setting for model invocation.
            guardrailIdentifier: Optional guardrail identifier.
            guardrailVersion: Optional guardrail version.
            performanceConfigLatency: Optional latency optimization setting.
            serviceTier: Optional Bedrock service tier.

        Returns:
            Model invocation response.

        """
        from botocraft.services.bedrock_runtime import ConversationManager

        manager = cast("ConversationManager", ConversationManager().using(self.session))
        return cast(
            "InvokeModelResponse",
            manager.invoke_model(
                cast("str", self.modelId),
                body=body,
                contentType=contentType,
                accept=accept,
                trace=trace,
                guardrailIdentifier=guardrailIdentifier,
                guardrailVersion=guardrailVersion,
                performanceConfigLatency=performanceConfigLatency,
                serviceTier=serviceTier,
            ),
        )

    def invoke_model_with_response_stream(
        self,
        body: bytes,
        contentType: str,
        *,
        accept: str | None = None,
        trace: Literal["ENABLED", "DISABLED", "ENABLED_FULL"] | None = None,
        guardrailIdentifier: str | None = None,
        guardrailVersion: str | None = None,
        performanceConfigLatency: Literal["standard", "optimized"] | None = None,
        serviceTier: Literal["priority", "default", "flex", "reserved"] | None = None,
    ) -> InvokeModelWithResponseStreamResponse:
        """
        Invoke this foundation model and stream raw Bedrock Runtime response.

        Args:
            body: Input body for model inference.
            contentType: MIME type of input body.

        Keyword Args:
            accept: Desired MIME type for streamed response body.
            trace: Optional trace setting for model invocation.
            guardrailIdentifier: Optional guardrail identifier.
            guardrailVersion: Optional guardrail version.
            performanceConfigLatency: Optional latency optimization setting.
            serviceTier: Optional Bedrock service tier.

        Returns:
            Iterable streaming model invocation response.

        """
        from botocraft.services.bedrock_runtime import ConversationManager

        manager = cast("ConversationManager", ConversationManager().using(self.session))
        return cast(
            "InvokeModelWithResponseStreamResponse",
            manager.invoke_model_with_response_stream(
                cast("str", self.modelId),
                body=body,
                contentType=contentType,
                accept=accept,
                trace=trace,
                guardrailIdentifier=guardrailIdentifier,
                guardrailVersion=guardrailVersion,
                performanceConfigLatency=performanceConfigLatency,
                serviceTier=serviceTier,
            ),
        )

    def start_async_invoke(
        self,
        modelInput: ModelInputPayload,
        outputDataConfig: AsyncInvokeOutputDataConfig,
        *,
        clientRequestToken: str | None = None,
        tags: list[dict[str, str]] | None = None,
    ) -> StartAsyncInvokeResponse:
        """
        Start async invocation for this foundation model.

        Args:
            modelInput: Input payload for asynchronous model invocation.
            outputDataConfig: Destination configuration for invocation output.

        Keyword Args:
            clientRequestToken: Optional idempotency token.
            tags: Optional AWS tags for invocation record.

        Returns:
            Async invocation start response.

        """
        from botocraft.services.bedrock_runtime import ConversationManager

        manager = cast("ConversationManager", ConversationManager().using(self.session))
        return cast(
            "StartAsyncInvokeResponse",
            manager.start_async_invoke(
                cast("str", self.modelId),
                modelInput=modelInput,
                outputDataConfig=outputDataConfig,
                clientRequestToken=clientRequestToken,
                tags=tags,  # type: ignore[arg-type]
            ),
        )

    def get_async_invoke(
        self,
        invocationArn: str,
    ) -> GetAsyncInvokeResponse:
        """
        Get async invocation details for this foundation model.

        Args:
            invocationArn: ARN of async invocation to inspect.

        Raises:
            ValueError: ``modelArn`` is missing on foundation model.
            LookupError: Async invocation belongs to different model ARN.

        Returns:
            Async invocation response for this model.

        """
        from botocraft.services.bedrock_runtime import ConversationManager

        model_arn = self._require_model_arn()
        manager = cast("ConversationManager", ConversationManager().using(self.session))
        response = cast(
            "GetAsyncInvokeResponse",
            manager.get_async_invoke(invocationArn),
        )
        if response.modelArn != model_arn:
            msg = (
                f"Async invocation modelArn mismatch: expected {model_arn}, "
                f"got {response.modelArn}."
            )
            raise LookupError(msg)
        return response

    def list_async_invokes(
        self,
        *,
        submitTimeAfter: datetime | None = None,
        submitTimeBefore: datetime | None = None,
        statusEquals: Literal["InProgress", "Completed", "Failed"] | None = None,
        maxResults: int | None = None,
        nextToken: str | None = None,
        sortBy: Literal["SubmissionTime"] | None = None,
        sortOrder: Literal["Ascending", "Descending"] | None = None,
    ) -> ListAsyncInvokesResponse:
        """
        List async invocations scoped to this foundation model.

        Filtering happens after AWS pagination, so returned summaries may be
        fewer than requested and may be empty even when ``nextToken`` exists.

        Keyword Args:
            submitTimeAfter: Lower bound for invocation submit time.
            submitTimeBefore: Upper bound for invocation submit time.
            statusEquals: Optional invocation status filter.
            maxResults: Maximum results to request from AWS page.
            nextToken: Pagination token from prior AWS page.
            sortBy: Sort key for AWS response ordering.
            sortOrder: Sort direction for AWS response ordering.

        Raises:
            ValueError: ``modelArn`` is missing on foundation model.

        Returns:
            Filtered async invocation list response for this model.

        """
        from botocraft.services.bedrock_runtime import ConversationManager

        model_arn = self._require_model_arn()
        manager = cast("ConversationManager", ConversationManager().using(self.session))
        response = cast(
            "ListAsyncInvokesResponse",
            manager.list_async_invokes(
                submitTimeAfter=submitTimeAfter,
                submitTimeBefore=submitTimeBefore,
                statusEquals=statusEquals,
                maxResults=maxResults,
                nextToken=nextToken,
                sortBy=sortBy,
                sortOrder=sortOrder,
            ),
        )
        summaries = [
            summary
            for summary in response.asyncInvokeSummaries or []
            if summary.modelArn == model_arn
        ]
        return cast(
            "ListAsyncInvokesResponse",
            response.model_copy(update={"asyncInvokeSummaries": summaries}),
        )

    def apply_guardrail(
        self,
        guardrail: Guardrail | str,
        content: list[GuardrailContentBlock],
        *,
        source: Literal["INPUT", "OUTPUT"] = "INPUT",
        outputScope: Literal["INTERVENTIONS", "FULL"] | None = None,
        guardrailVersion: str | None = None,
    ) -> GuardrailApplication:
        """
        Apply a guardrail to content while keeping API model-centric.

        This is a convenience wrapper over Guardrails runtime behavior. The
        foundation model identity is not sent to AWS for this call.

        Args:
            guardrail: Guardrail object or raw guardrail identifier.
            content: Guardrail content payload.

        Keyword Args:
            source: Whether content is model input or output.
            outputScope: Optional guardrail output verbosity.
            guardrailVersion: Explicit guardrail version override.

        Raises:
            ValueError: Guardrail version is missing.

        Returns:
            Guardrail application response.

        """
        from botocraft.services.bedrock_runtime import GuardrailApplicationManager

        guardrail_identifier, resolved_guardrail_version = (
            _guardrail_identifier_and_version(guardrail, guardrailVersion)
        )
        manager = cast(
            "GuardrailApplicationManager",
            GuardrailApplicationManager().using(self.session),
        )
        return cast(
            "GuardrailApplication",
            manager.apply(
                guardrail_identifier,
                resolved_guardrail_version,
                source=source,
                content=content,
                outputScope=outputScope,
            ),
        )


class GuardrailRuntimeMixin:
    """
    Convenience Bedrock Runtime helpers for guardrail instances.

    This mixin exposes runtime `ApplyGuardrail` behavior on guardrail model
    itself so callers can work from fetched guardrail objects directly.
    """

    #: Boto3 session attached by Botocraft model managers.
    session: Session | None
    #: Guardrail identifier for runtime operations.
    guardrailId: str | None
    #: Guardrail version for runtime operations.
    version: str | None

    def apply(
        self,
        content: list[GuardrailContentBlock],
        *,
        source: Literal["INPUT", "OUTPUT"] = "INPUT",
        outputScope: Literal["INTERVENTIONS", "FULL"] | None = None,
    ) -> GuardrailApplication:
        """
        Apply this guardrail to content through Bedrock Runtime.

        Args:
            content: Guardrail content payload.

        Keyword Args:
            source: Whether content is model input or output.
            outputScope: Optional guardrail output verbosity.

        Raises:
            ValueError: Guardrail version is missing.

        Returns:
            Guardrail application response.

        """
        from botocraft.services.bedrock_runtime import GuardrailApplicationManager

        guardrail_identifier, guardrail_version = _guardrail_identifier_and_version(
            cast("Guardrail", self),
            self.version,
        )
        manager = cast(
            "GuardrailApplicationManager",
            GuardrailApplicationManager().using(self.session),
        )
        return cast(
            "GuardrailApplication",
            manager.apply(
                guardrail_identifier,
                guardrail_version,
                source=source,
                content=content,
                outputScope=outputScope,
            ),
        )
