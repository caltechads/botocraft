from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from botocraft.services.bedrock import FoundationModel, Guardrail
from botocraft.services.bedrock_runtime import (
    AsyncInvokeOutputDataConfig,
    AsyncInvokeS3OutputDataConfig,
    AsyncInvokeSummary,
    Conversation,
    ConversationManager,
    ConverseStreamResponse,
    Document,
    GetAsyncInvokeResponse,
    GuardrailApplication,
    GuardrailApplicationManager,
    InvokeModelResponse,
    InvokeModelWithResponseStreamResponse,
    JsonSchemaDefinition,
    ListAsyncInvokesResponse,
    StartAsyncInvokeResponse,
    TokenCount,
    ToolInputSchema,
    ToolResultContentBlock,
)


class TestConversationManager:
    @patch("boto3.client")
    def test_close(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = ConversationManager()
        manager.close()

        mock_client.close.assert_called_once_with()

    @patch("boto3.client")
    def test_converse(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "hello"}],
                }
            },
            "stopReason": "end_turn",
            "usage": {
                "inputTokens": 10,
                "outputTokens": 20,
                "totalTokens": 30,
            },
            "metrics": {"latencyMs": 123},
        }
        mock_boto3_client.return_value = mock_client

        manager = ConversationManager()
        conversation = manager.converse(
            "model-1",
            messages=[{"role": "user", "content": [{"text": "hello"}]}],
        )

        mock_client.converse.assert_called_once_with(
            modelId="model-1",
            messages=[{"role": "user", "content": [{"text": "hello"}]}],
        )
        assert ConversationManager.service_name == "bedrock-runtime"
        assert isinstance(conversation, Conversation)
        assert conversation.output.message.role == "assistant"

    @patch("boto3.client")
    def test_count_tokens(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.count_tokens.return_value = {"inputTokens": 42}
        mock_boto3_client.return_value = mock_client

        manager = ConversationManager()
        token_count = manager.count_tokens(
            "model-1",
            input={"invokeModel": {"body": "{}"}},
        )

        mock_client.count_tokens.assert_called_once_with(
            modelId="model-1",
            input={"invokeModel": {"body": "{}"}},
        )
        assert isinstance(token_count, TokenCount)
        assert token_count.inputTokens == 42

    @patch("boto3.client")
    def test_converse_stream(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.converse_stream.return_value = {
            "stream": {"messageStart": {"role": "assistant"}}
        }
        mock_boto3_client.return_value = mock_client

        manager = ConversationManager()
        response = manager.converse_stream(
            "model-1",
            messages=[{"role": "user", "content": [{"text": "hello"}]}],
        )

        mock_client.converse_stream.assert_called_once_with(
            modelId="model-1",
            messages=[{"role": "user", "content": [{"text": "hello"}]}],
        )
        assert isinstance(response, ConverseStreamResponse)
        assert response.stream.messageStart.role == "assistant"

    @patch("boto3.client")
    def test_invoke_model(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = {
            "body": b'{"answer":"hello"}',
            "contentType": "application/json",
        }
        mock_boto3_client.return_value = mock_client

        manager = ConversationManager()
        response = manager.invoke_model(
            "model-1",
            body=b'{"prompt":"hello"}',
            contentType="application/json",
        )

        mock_client.invoke_model.assert_called_once_with(
            modelId="model-1",
            body=b'{"prompt":"hello"}',
            contentType="application/json",
        )
        assert isinstance(response, InvokeModelResponse)
        assert response.body == b'{"answer":"hello"}'

    @patch("boto3.client")
    def test_invoke_model_with_response_stream(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.invoke_model_with_response_stream.return_value = {
            "body": {"chunk": {"bytes": b"chunk-1"}},
            "contentType": "application/json",
        }
        mock_boto3_client.return_value = mock_client

        manager = ConversationManager()
        response = manager.invoke_model_with_response_stream(
            "model-1",
            body=b'{"prompt":"hello"}',
            contentType="application/json",
        )

        mock_client.invoke_model_with_response_stream.assert_called_once_with(
            modelId="model-1",
            body=b'{"prompt":"hello"}',
            contentType="application/json",
        )
        assert isinstance(response, InvokeModelWithResponseStreamResponse)
        assert response.body.chunk.data == b"chunk-1"

    @patch("boto3.client")
    def test_start_async_invoke(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.start_async_invoke.return_value = {
            "invocationArn": "arn:aws:bedrock:us-west-2:123:async-invoke/abc"
        }
        mock_boto3_client.return_value = mock_client

        manager = ConversationManager()
        response = manager.start_async_invoke(
            "model-1",
            modelInput={},
            outputDataConfig={"s3OutputDataConfig": {"s3Uri": "s3://bucket/output"}},
        )

        mock_client.start_async_invoke.assert_called_once_with(
            modelId="model-1",
            modelInput={},
            outputDataConfig={"s3OutputDataConfig": {"s3Uri": "s3://bucket/output"}},
        )
        assert isinstance(response, StartAsyncInvokeResponse)
        assert response.invocationArn.endswith("/abc")

    @patch("boto3.client")
    def test_get_async_invoke(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.get_async_invoke.return_value = {
            "invocationArn": "arn:aws:bedrock:us-west-2:123:async-invoke/abc",
            "modelArn": "arn:aws:bedrock:us-west-2::foundation-model/model-1",
            "status": "Completed",
            "submitTime": datetime(2024, 1, 1, tzinfo=UTC),
            "outputDataConfig": {"s3OutputDataConfig": {"s3Uri": "s3://bucket/output"}},
        }
        mock_boto3_client.return_value = mock_client

        manager = ConversationManager()
        response = manager.get_async_invoke(
            "arn:aws:bedrock:us-west-2:123:async-invoke/abc"
        )

        mock_client.get_async_invoke.assert_called_once_with(
            invocationArn="arn:aws:bedrock:us-west-2:123:async-invoke/abc"
        )
        assert isinstance(response, GetAsyncInvokeResponse)
        assert response.modelArn == "arn:aws:bedrock:us-west-2::foundation-model/model-1"

    @patch("boto3.client")
    def test_list_async_invokes(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.list_async_invokes.return_value = {
            "nextToken": "token-1",
            "asyncInvokeSummaries": [
                {
                    "invocationArn": "arn:aws:bedrock:us-west-2:123:async-invoke/abc",
                    "modelArn": "arn:aws:bedrock:us-west-2::foundation-model/model-1",
                    "submitTime": datetime(2024, 1, 1, tzinfo=UTC),
                    "outputDataConfig": {
                        "s3OutputDataConfig": {"s3Uri": "s3://bucket/output"}
                    },
                }
            ],
        }
        mock_boto3_client.return_value = mock_client

        manager = ConversationManager()
        response = manager.list_async_invokes()

        mock_client.list_async_invokes.assert_called_once_with()
        assert isinstance(response, ListAsyncInvokesResponse)
        assert response.nextToken == "token-1"
        assert response.asyncInvokeSummaries[0].modelArn.endswith("model-1")


class TestGuardrailApplicationManager:
    @patch("boto3.client")
    def test_apply(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.apply_guardrail.return_value = {
            "usage": {
                "topicPolicyUnits": 0,
                "contentPolicyUnits": 0,
                "wordPolicyUnits": 0,
                "sensitiveInformationPolicyUnits": 0,
                "sensitiveInformationPolicyFreeUnits": 0,
                "contextualGroundingPolicyUnits": 0,
            },
            "action": "NONE",
            "outputs": [{"text": "clean"}],
            "assessments": [],
        }
        mock_boto3_client.return_value = mock_client

        manager = GuardrailApplicationManager()
        result = manager.apply(
            "gr-123",
            "1",
            source="INPUT",
            content=[{"text": {"text": "hello"}}],
        )

        mock_client.apply_guardrail.assert_called_once_with(
            guardrailIdentifier="gr-123",
            guardrailVersion="1",
            source="INPUT",
            content=[{"text": {"text": "hello"}}],
        )
        assert GuardrailApplicationManager.service_name == "bedrock-runtime"
        assert isinstance(result, GuardrailApplication)
        assert result.action == "NONE"


class TestBedrockRuntimeMixins:
    def test_foundation_model_close(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)
        with (
            patch.object(
                ConversationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                ConversationManager,
                "close",
                autospec=True,
                return_value=None,
            ) as close,
        ):
            model.close()

        using.assert_called_once()
        close.assert_called_once()

    def test_foundation_model_converse(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)
        conversation = Conversation.model_construct()
        with (
            patch.object(
                ConversationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                ConversationManager,
                "converse",
                autospec=True,
                return_value=conversation,
            ) as converse,
        ):
            result = model.converse(
                messages=[{"role": "user", "content": [{"text": "hello"}]}]
            )

        using.assert_called_once()
        assert converse.call_args.args[1] == "model-1"
        assert converse.call_args.kwargs == {
            "messages": [{"role": "user", "content": [{"text": "hello"}]}],
            "system": None,
            "toolConfig": None,
            "inferenceConfig": None,
            "guardrailConfig": None,
            "additionalModelRequestFields": None,
            "promptVariables": None,
            "additionalModelResponseFieldPaths": None,
            "requestMetadata": None,
            "performanceConfig": None,
            "serviceTier": None,
            "outputConfig": None,
        }
        assert result is conversation

    def test_foundation_model_count_tokens(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)
        token_count = TokenCount.model_construct(inputTokens=9)
        with (
            patch.object(
                ConversationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                ConversationManager,
                "count_tokens",
                autospec=True,
                return_value=token_count,
            ) as count_tokens,
        ):
            result = model.count_tokens({"invokeModel": {"body": "{}"}})

        using.assert_called_once()
        assert count_tokens.call_args.args[1] == "model-1"
        assert count_tokens.call_args.kwargs == {
            "input": {"invokeModel": {"body": "{}"}}
        }
        assert result is token_count

    def test_foundation_model_converse_stream_builds_guardrail_config(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)
        guardrail = Guardrail.model_construct(
            guardrailId="gr-123",
            version="1",
            session=None,
        )
        response = ConverseStreamResponse.model_construct()
        with (
            patch.object(
                ConversationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ),
            patch.object(
                ConversationManager,
                "converse_stream",
                autospec=True,
                return_value=response,
            ) as converse_stream,
        ):
            result = model.converse_stream(
                messages=[{"role": "user", "content": [{"text": "hello"}]}],
                guardrail=guardrail,
            )

        assert converse_stream.call_args.args[1] == "model-1"
        assert converse_stream.call_args.kwargs["guardrailConfig"] == {
            "guardrailIdentifier": "gr-123",
            "guardrailVersion": "1",
        }
        assert result is response

    def test_foundation_model_invoke_model(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)
        response = InvokeModelResponse.model_construct(
            body=b"{}",
            contentType="application/json",
        )
        with (
            patch.object(
                ConversationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                ConversationManager,
                "invoke_model",
                autospec=True,
                return_value=response,
            ) as invoke_model,
        ):
            result = model.invoke_model(
                body=b'{"prompt":"hello"}',
                contentType="application/json",
            )

        using.assert_called_once()
        assert invoke_model.call_args.args[1] == "model-1"
        assert invoke_model.call_args.kwargs == {
            "body": b'{"prompt":"hello"}',
            "contentType": "application/json",
            "accept": None,
            "trace": None,
            "guardrailIdentifier": None,
            "guardrailVersion": None,
            "performanceConfigLatency": None,
            "serviceTier": None,
        }
        assert result is response

    def test_foundation_model_get_async_invoke_requires_model_arn(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)

        with pytest.raises(ValueError, match="modelArn"):
            model.get_async_invoke("arn:aws:bedrock:us-west-2:123:async-invoke/abc")

    def test_foundation_model_get_async_invoke_rejects_model_mismatch(self):
        model = FoundationModel.model_construct(
            modelId="model-1",
            modelArn="arn:aws:bedrock:us-west-2::foundation-model/model-1",
            session=None,
        )
        response = GetAsyncInvokeResponse.model_construct(
            invocationArn="arn:aws:bedrock:us-west-2:123:async-invoke/abc",
            modelArn="arn:aws:bedrock:us-west-2::foundation-model/model-2",
            status="Completed",
            submitTime=datetime(2024, 1, 1, tzinfo=UTC),
            outputDataConfig=AsyncInvokeOutputDataConfig.model_construct(
                s3OutputDataConfig=AsyncInvokeS3OutputDataConfig.model_construct(
                    s3Uri="s3://bucket/output"
                )
            ),
        )
        with (
            patch.object(
                ConversationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ),
            patch.object(
                ConversationManager,
                "get_async_invoke",
                autospec=True,
                return_value=response,
            ),
            pytest.raises(LookupError, match="modelArn"),
        ):
            model.get_async_invoke("arn:aws:bedrock:us-west-2:123:async-invoke/abc")

    def test_foundation_model_list_async_invokes_requires_model_arn(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)

        with pytest.raises(ValueError, match="modelArn"):
            model.list_async_invokes()

    def test_foundation_model_list_async_invokes_filters_by_model_arn(self):
        model = FoundationModel.model_construct(
            modelId="model-1",
            modelArn="arn:aws:bedrock:us-west-2::foundation-model/model-1",
            session=None,
        )
        response = ListAsyncInvokesResponse.model_construct(
            nextToken="token-1",
            asyncInvokeSummaries=[
                AsyncInvokeSummary.model_construct(
                    invocationArn="arn:aws:bedrock:us-west-2:123:async-invoke/one",
                    modelArn="arn:aws:bedrock:us-west-2::foundation-model/model-1",
                    submitTime=datetime(2024, 1, 1, tzinfo=UTC),
                    outputDataConfig=AsyncInvokeOutputDataConfig.model_construct(
                        s3OutputDataConfig=AsyncInvokeS3OutputDataConfig.model_construct(
                            s3Uri="s3://bucket/one"
                        )
                    ),
                ),
                AsyncInvokeSummary.model_construct(
                    invocationArn="arn:aws:bedrock:us-west-2:123:async-invoke/two",
                    modelArn="arn:aws:bedrock:us-west-2::foundation-model/model-2",
                    submitTime=datetime(2024, 1, 2, tzinfo=UTC),
                    outputDataConfig=AsyncInvokeOutputDataConfig.model_construct(
                        s3OutputDataConfig=AsyncInvokeS3OutputDataConfig.model_construct(
                            s3Uri="s3://bucket/two"
                        )
                    ),
                ),
            ],
        )
        with (
            patch.object(
                ConversationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ),
            patch.object(
                ConversationManager,
                "list_async_invokes",
                autospec=True,
                return_value=response,
            ),
        ):
            result = model.list_async_invokes()

        assert result.nextToken == "token-1"
        assert [summary.invocationArn for summary in result.asyncInvokeSummaries] == [
            "arn:aws:bedrock:us-west-2:123:async-invoke/one"
        ]

    def test_guardrail_apply(self):
        guardrail = Guardrail.model_construct(
            guardrailId="gr-123",
            version="1",
            session=None,
        )
        application = GuardrailApplication.model_construct(action="NONE")
        with (
            patch.object(
                GuardrailApplicationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                GuardrailApplicationManager,
                "apply",
                autospec=True,
                return_value=application,
            ) as apply_guardrail,
        ):
            result = guardrail.apply(
                content=[{"text": {"text": "hello"}}],
                source="INPUT",
            )

        using.assert_called_once()
        assert apply_guardrail.call_args.args[1:3] == ("gr-123", "1")
        assert apply_guardrail.call_args.kwargs == {
            "source": "INPUT",
            "content": [{"text": {"text": "hello"}}],
            "outputScope": None,
        }
        assert result is application


class TestBedrockRuntimeShadowedFieldAliases:
    def test_shadowed_runtime_fields_use_aliases(self):
        document = Document.model_construct(session=None)
        tool_result = ToolResultContentBlock.model_construct(
            jsonData=document,
            session=None,
        )
        tool_input_schema = ToolInputSchema.model_construct(
            jsonSchema=document,
            session=None,
        )
        json_schema = JsonSchemaDefinition.model_validate(
            {"schema": '{"type":"object"}', "name": "answer-shape"}
        )

        assert ToolResultContentBlock.model_fields["jsonData"].alias == "json"
        assert tool_result.jsonData is document
        assert tool_result.model_dump(by_alias=True)["json"] == {}
        assert ToolInputSchema.model_fields["jsonSchema"].alias == "json"
        assert tool_input_schema.jsonSchema is document
        assert tool_input_schema.model_dump(by_alias=True)["json"] == {}
        assert json_schema.schemaDefinition == '{"type":"object"}'
        assert json_schema.model_dump(by_alias=True)["schema"] == '{"type":"object"}'

    def test_foundation_model_apply_guardrail(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)
        guardrail = Guardrail.model_construct(
            guardrailId="gr-123",
            version="1",
            session=None,
        )
        application = GuardrailApplication.model_construct(action="NONE")
        with (
            patch.object(
                GuardrailApplicationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                GuardrailApplicationManager,
                "apply",
                autospec=True,
                return_value=application,
            ) as apply_guardrail,
        ):
            result = model.apply_guardrail(
                guardrail,
                [{"text": {"text": "hello"}}],
                source="INPUT",
            )

        using.assert_called_once()
        assert apply_guardrail.call_args.args[1:3] == ("gr-123", "1")
        assert apply_guardrail.call_args.kwargs == {
            "source": "INPUT",
            "content": [{"text": {"text": "hello"}}],
            "outputScope": None,
        }
        assert result is application

    def test_foundation_model_converse_builds_guardrail_config(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)
        guardrail = Guardrail.model_construct(
            guardrailId="gr-123",
            version="1",
            session=None,
        )
        conversation = Conversation.model_construct()
        with (
            patch.object(
                ConversationManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ),
            patch.object(
                ConversationManager,
                "converse",
                autospec=True,
                return_value=conversation,
            ) as converse,
        ):
            result = model.converse(
                messages=[{"role": "user", "content": [{"text": "hello"}]}],
                guardrail=guardrail,
            )

        assert converse.call_args.kwargs["guardrailConfig"] == {
            "guardrailIdentifier": "gr-123",
            "guardrailVersion": "1",
        }
        assert result is conversation

    def test_foundation_model_converse_rejects_conflicting_guardrail_args(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)
        guardrail = Guardrail.model_construct(
            guardrailId="gr-123",
            version="1",
            session=None,
        )

        with pytest.raises(ValueError, match="guardrail"):
            model.converse(
                messages=[{"role": "user", "content": [{"text": "hello"}]}],
                guardrail=guardrail,
                guardrailConfig={"guardrailIdentifier": "other"},
            )

    def test_foundation_model_apply_guardrail_requires_version(self):
        model = FoundationModel.model_construct(modelId="model-1", session=None)

        with pytest.raises(ValueError, match="guardrailVersion"):
            model.apply_guardrail(
                "gr-123",
                [{"text": {"text": "hello"}}],
                source="INPUT",
            )
