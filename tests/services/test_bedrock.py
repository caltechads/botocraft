import subprocess
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.bedrock import (
    AutomatedReasoningPolicy,
    AutomatedReasoningPolicyDefinition,
    AutomatedReasoningPolicyManager,
    CustomModel,
    CustomModelManager,
    FoundationModel,
    FoundationModelAgreementManager,
    FoundationModelManager,
    Guardrail,
    GuardrailManager,
    ModelInvocationLoggingConfiguration,
    ModelInvocationLoggingConfigurationManager,
    Offer,
    ResourcePolicy,
    ResourcePolicyManager,
)


class TestFoundationModelManager:
    @patch("boto3.client")
    def test_get_foundation_model(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.get_foundation_model.return_value = {
            "modelDetails": {
                "modelArn": "arn:aws:bedrock:us-west-2::foundation-model/test",
                "modelId": "test",
                "modelName": "Test Model",
                "providerName": "OpenAI",
                "inputModalities": ["TEXT"],
                "outputModalities": ["TEXT"],
                "responseStreamingSupported": True,
                "customizationsSupported": [],
                "inferenceTypesSupported": ["ON_DEMAND"],
                "modelLifecycle": {"status": "ACTIVE"},
            }
        }
        mock_boto3_client.return_value = mock_client

        manager = FoundationModelManager()
        model = manager.get("test")

        mock_client.get_foundation_model.assert_called_once_with(modelIdentifier="test")
        assert isinstance(model, FoundationModel)
        assert model.modelId == "test"

    @patch("boto3.client")
    def test_list_foundation_models(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.list_foundation_models.return_value = {
            "modelSummaries": [
                {
                    "modelArn": "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-haiku",
                    "modelId": "anthropic.claude-3-haiku",
                    "modelName": "Claude 3 Haiku",
                    "providerName": "Anthropic",
                    "inputModalities": ["TEXT"],
                    "outputModalities": ["TEXT"],
                    "responseStreamingSupported": True,
                    "customizationsSupported": [],
                    "inferenceTypesSupported": ["ON_DEMAND"],
                    "modelLifecycle": {"status": "ACTIVE"},
                }
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = FoundationModelManager()
        models = manager.list(byProvider="Anthropic")

        mock_client.list_foundation_models.assert_called_once_with(
            byProvider="Anthropic"
        )
        assert isinstance(models, PrimaryBoto3ModelQuerySet)
        assert len(models) == 1
        assert isinstance(models[0], FoundationModel)
        assert models[0].providerName == "Anthropic"

    @patch("boto3.client")
    def test_list_foundation_models_accepts_new_bedrock_capability_values(
        self,
        mock_boto3_client,
    ):
        mock_client = MagicMock()
        mock_client.list_foundation_models.return_value = {
            "modelSummaries": [
                {
                    "modelArn": "arn:aws:bedrock:us-west-2::foundation-model/openai.gpt-4.1-mini",
                    "modelId": "openai.gpt-4.1-mini",
                    "modelName": "GPT-4.1 mini",
                    "providerName": "OpenAI",
                    "inputModalities": ["TEXT", "VIDEO"],
                    "outputModalities": ["TEXT", "IMAGE"],
                    "responseStreamingSupported": True,
                    "customizationsSupported": ["DISTILLATION"],
                    "inferenceTypesSupported": ["ON_DEMAND", "INFERENCE_PROFILE"],
                    "modelLifecycle": {"status": "ACTIVE"},
                }
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = FoundationModelManager()
        models = manager.list()

        assert len(models) == 1
        assert models[0].inputModalities == ["TEXT", "VIDEO"]
        assert models[0].inferenceTypesSupported == [
            "ON_DEMAND",
            "INFERENCE_PROFILE",
        ]


class TestFoundationModelAgreementManager:
    @patch("boto3.client")
    def test_list_offers(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.list_foundation_model_agreement_offers.return_value = {
            "modelId": "test-model",
            "offers": [
                {
                    "offerId": "offer-1",
                    "offerToken": "token-1",
                    "termDetails": {
                        "usageBasedPricingTerm": {"rateCard": []},
                        "legalTerm": {},
                        "supportTerm": {},
                    },
                }
            ],
        }
        mock_boto3_client.return_value = mock_client

        manager = FoundationModelAgreementManager()
        offers = manager.list_offers("test-model")

        mock_client.list_foundation_model_agreement_offers.assert_called_once_with(
            modelId="test-model"
        )
        assert len(offers) == 1
        assert isinstance(offers[0], Offer)
        assert offers[0].offerToken == "token-1"


class TestResourcePolicyManager:
    @patch("boto3.client")
    def test_get_resource_policy_returns_bespoke_model(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.get_resource_policy.return_value = {
            "resourcePolicy": '{"Version":"2012-10-17"}'
        }
        mock_boto3_client.return_value = mock_client

        manager = ResourcePolicyManager()
        policy = manager.get("arn:aws:bedrock:us-west-2:123456789012:guardrail/gr-123")

        mock_client.get_resource_policy.assert_called_once_with(
            resourceArn="arn:aws:bedrock:us-west-2:123456789012:guardrail/gr-123"
        )
        assert isinstance(policy, ResourcePolicy)
        assert policy.resourcePolicy == '{"Version":"2012-10-17"}'


class TestCustomModelManager:
    @patch("boto3.client")
    def test_get_custom_model_uses_summary_shape(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.get_custom_model.return_value = {
            "modelArn": "arn:aws:bedrock:us-west-2:123456789012:custom-model/test",
            "modelName": "test-model",
            "creationTime": datetime.now(tz=timezone.utc),
            "baseModelArn": "arn:aws:bedrock:us-west-2::foundation-model/base",
            "customizationType": "FINE_TUNING",
            "modelStatus": "Active",
        }
        mock_boto3_client.return_value = mock_client

        manager = CustomModelManager()
        model = manager.get(
            "arn:aws:bedrock:us-west-2:123456789012:custom-model/test"
        )

        assert isinstance(model, CustomModel)
        assert model.modelName == "test-model"
        assert model.baseModelName is None
        assert model.ownerAccountId is None


class TestGuardrailVersionMethods:
    @patch("boto3.client")
    def test_manager_create_version(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.create_guardrail_version.return_value = {
            "guardrailId": "gr-123",
            "version": "1",
        }
        mock_boto3_client.return_value = mock_client

        manager = GuardrailManager()
        version = manager.create_version("gr-123", description="snapshot")

        mock_client.create_guardrail_version.assert_called_once_with(
            guardrailIdentifier="gr-123",
            description="snapshot",
        )
        assert version == "1"

    def test_model_create_version_shortcut(self):
        guardrail = Guardrail.model_construct(guardrailId="gr-123", session=None)
        with (
            patch.object(GuardrailManager, "using", autospec=True, side_effect=lambda self, _session: self) as using,
            patch.object(GuardrailManager, "create_version", autospec=True, return_value="2") as create_version,
        ):
            version = guardrail.create_version("release")

        using.assert_called_once()
        create_version.assert_called_once()
        _, guardrail_id = create_version.call_args.args[:2]
        assert guardrail_id == "gr-123"
        assert create_version.call_args.kwargs == {"description": "release"}
        assert version == "2"


class TestAutomatedReasoningPolicyVersionMethods:
    @patch("boto3.client")
    def test_manager_create_version(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.create_automated_reasoning_policy_version.return_value = {
            "policyArn": "arn:aws:bedrock:us-west-2:123456789012:policy/test",
            "version": "2",
            "name": "test-policy",
            "definitionHash": "abc123",
            "createdAt": datetime.now(tz=timezone.utc),
        }
        mock_boto3_client.return_value = mock_client

        manager = AutomatedReasoningPolicyManager()
        version = manager.create_version("policy-arn", "abc123")

        mock_client.create_automated_reasoning_policy_version.assert_called_once_with(
            policyArn="policy-arn",
            lastUpdatedDefinitionHash="abc123",
        )
        assert version == "2"

    @patch("boto3.client")
    def test_manager_export_version(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.export_automated_reasoning_policy_version.return_value = {
            "policyDefinition": {}
        }
        mock_boto3_client.return_value = mock_client

        manager = AutomatedReasoningPolicyManager()
        definition = manager.export_version("policy-arn")

        mock_client.export_automated_reasoning_policy_version.assert_called_once_with(
            policyArn="policy-arn"
        )
        assert isinstance(definition, AutomatedReasoningPolicyDefinition)

    def test_model_shortcuts(self):
        policy = AutomatedReasoningPolicy.model_construct(
            policyArn="policy-arn", session=None
        )
        with (
            patch.object(AutomatedReasoningPolicyManager, "using", autospec=True, side_effect=lambda self, _session: self) as using,
            patch.object(
                AutomatedReasoningPolicyManager,
                "create_version",
                autospec=True,
                return_value="3",
            ) as create_version,
            patch.object(
                AutomatedReasoningPolicyManager,
                "export_version",
                autospec=True,
                return_value=AutomatedReasoningPolicyDefinition.model_construct(),
            ) as export_version,
        ):
            version = policy.create_version("hash-1")
            definition = policy.export_version()

        assert using.call_count == 2
        create_version.assert_called_once()
        _, policy_arn, last_hash = create_version.call_args.args[:3]
        assert policy_arn == "policy-arn"
        assert last_hash == "hash-1"
        export_version.assert_called_once()
        _, export_policy_arn = export_version.call_args.args[:2]
        assert export_policy_arn == "policy-arn"
        assert version == "3"
        assert isinstance(definition, AutomatedReasoningPolicyDefinition)


class TestBedrockShadowedFieldAliases:
    def test_primary_model_name_property_uses_renamed_field(self):
        guardrail = Guardrail.model_construct(
            guardrailId="gr-123",
            guardrailName="Test Guardrail",
            session=None,
        )
        policy = AutomatedReasoningPolicy.model_construct(
            policyArn="policy-arn",
            policyName="Test Policy",
            session=None,
        )

        assert guardrail.name == "Test Guardrail"
        assert guardrail.model_dump(by_alias=True)["name"] == "Test Guardrail"
        assert policy.name == "Test Policy"
        assert policy.model_dump(by_alias=True)["name"] == "Test Policy"

    def test_service_imports_do_not_emit_shadow_warnings(self):
        result = subprocess.run(
            [sys.executable, "-Wdefault", "-c", "from botocraft.services import *"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert "shadows an attribute" not in result.stderr


class TestModelInvocationLoggingConfigurationManager:
    @patch("boto3.client")
    def test_get_logging_configuration(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.get_model_invocation_logging_configuration.return_value = {
            "loggingConfig": {
                "textDataDeliveryEnabled": True,
                "imageDataDeliveryEnabled": False,
            }
        }
        mock_boto3_client.return_value = mock_client

        manager = ModelInvocationLoggingConfigurationManager()
        config = manager.get()

        mock_client.get_model_invocation_logging_configuration.assert_called_once_with()
        assert isinstance(config, ModelInvocationLoggingConfiguration)
        assert config.textDataDeliveryEnabled is True
