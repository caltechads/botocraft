import subprocess
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.bedrock import (
    AutomatedReasoningPolicy,
    AutomatedReasoningPolicyAnnotations,
    AutomatedReasoningPolicyAnnotationsManager,
    AutomatedReasoningPolicyBuildWorkflow,
    AutomatedReasoningPolicyBuildWorkflowManager,
    AutomatedReasoningPolicyBuildWorkflowResultAssets,
    AutomatedReasoningPolicyBuildWorkflowResultAssetsManager,
    AutomatedReasoningPolicyDefinition,
    AutomatedReasoningPolicyManager,
    AutomatedReasoningPolicyNextScenario,
    AutomatedReasoningPolicyNextScenarioManager,
    AutomatedReasoningPolicyTestCase,
    AutomatedReasoningPolicyTestCaseManager,
    AutomatedReasoningPolicyTestResult,
    AutomatedReasoningPolicyTestResultManager,
    BedrockVpcConfig,
    CustomModel,
    CustomModelManager,
    EnforcedGuardrailsConfiguration,
    EvaluationJob,
    FoundationModel,
    FoundationModelAgreementManager,
    FoundationModelManager,
    Guardrail,
    GuardrailManager,
    InferenceProfile,
    InferenceProfileModel,
    ModelCustomizationJob,
    ModelInvocationJob,
    ModelInvocationLoggingConfiguration,
    ModelInvocationLoggingConfigurationManager,
    Offer,
    PromptRouter,
    PromptRouterTargetModel,
    ResourcePolicy,
    ResourcePolicyManager,
)
from botocraft.services.ec2 import (
    SecurityGroup,
    SecurityGroupManager,
    Subnet,
    SubnetManager,
)
from botocraft.services.iam import IAMRole, IAMRoleManager
from botocraft.services.kms import KMSKey, KMSKeyManager
from botocraft.services.logs import LogGroup, LogGroupManager
from botocraft.services.s3 import Bucket, BucketManager


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


class TestBedrockRelations:
    def test_custom_model_base_model_relation(self):
        model = CustomModel.model_construct(
            modelArn="arn:aws:bedrock:us-west-2:123456789012:custom-model/test",
            baseModelArn="arn:aws:bedrock:us-west-2::foundation-model/base",
            session=None,
        )
        foundation_model = FoundationModel.model_construct(
            modelId="base",
            session=None,
        )

        with (
            patch.object(
                FoundationModelManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                FoundationModelManager,
                "get",
                autospec=True,
                return_value=foundation_model,
            ) as get,
        ):
            related = model.base_model

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {
            "modelId": "arn:aws:bedrock:us-west-2::foundation-model/base",
        }
        assert related is foundation_model

    def test_build_workflow_policy_relation(self):
        workflow = AutomatedReasoningPolicyBuildWorkflow.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            session=None,
        )
        policy = AutomatedReasoningPolicy.model_construct(
            policyArn="policy-arn",
            session=None,
        )

        with (
            patch.object(
                AutomatedReasoningPolicyManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                AutomatedReasoningPolicyManager,
                "get",
                autospec=True,
                return_value=policy,
            ) as get,
        ):
            related = workflow.policy

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {"policyArn": "policy-arn"}
        assert related is policy

    def test_build_workflow_result_assets_policy_relation(self):
        assets = AutomatedReasoningPolicyBuildWorkflowResultAssets.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            session=None,
        )
        policy = AutomatedReasoningPolicy.model_construct(
            policyArn="policy-arn",
            session=None,
        )

        with (
            patch.object(
                AutomatedReasoningPolicyManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                AutomatedReasoningPolicyManager,
                "get",
                autospec=True,
                return_value=policy,
            ) as get,
        ):
            related = assets.policy

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {"policyArn": "policy-arn"}
        assert related is policy

    def test_build_workflow_result_assets_build_workflow_relation(self):
        assets = AutomatedReasoningPolicyBuildWorkflowResultAssets.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            session=None,
        )
        workflow = AutomatedReasoningPolicyBuildWorkflow.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            session=None,
        )

        with (
            patch.object(
                AutomatedReasoningPolicyBuildWorkflowManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                AutomatedReasoningPolicyBuildWorkflowManager,
                "get",
                autospec=True,
                return_value=workflow,
            ) as get,
        ):
            related = assets.build_workflow

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {
            "policyArn": "policy-arn",
            "buildWorkflowId": "workflow-1",
        }
        assert related is workflow

    def test_annotations_policy_relation(self):
        annotations = AutomatedReasoningPolicyAnnotations.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            policyName="test-policy",
            session=None,
        )
        policy = AutomatedReasoningPolicy.model_construct(
            policyArn="policy-arn",
            session=None,
        )

        with (
            patch.object(
                AutomatedReasoningPolicyManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                AutomatedReasoningPolicyManager,
                "get",
                autospec=True,
                return_value=policy,
            ) as get,
        ):
            related = annotations.policy

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {"policyArn": "policy-arn"}
        assert related is policy

    def test_annotations_build_workflow_relation(self):
        annotations = AutomatedReasoningPolicyAnnotations.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            policyName="test-policy",
            session=None,
        )
        workflow = AutomatedReasoningPolicyBuildWorkflow.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            session=None,
        )

        with (
            patch.object(
                AutomatedReasoningPolicyBuildWorkflowManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                AutomatedReasoningPolicyBuildWorkflowManager,
                "get",
                autospec=True,
                return_value=workflow,
            ) as get,
        ):
            related = annotations.build_workflow

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {
            "policyArn": "policy-arn",
            "buildWorkflowId": "workflow-1",
        }
        assert related is workflow

    def test_evaluation_job_role_relation(self):
        job = EvaluationJob.model_construct(
            jobArn="job-arn",
            jobName="eval-job",
            status="Completed",
            jobType="Human",
            creationTime=datetime.now(tz=timezone.utc),
            roleArn="arn:aws:iam::123456789012:role/service-role/bedrock-eval-role",
            session=None,
        )
        role = IAMRole.model_construct(
            RoleName="service-role/bedrock-eval-role",
            Arn="arn:aws:iam::123456789012:role/service-role/bedrock-eval-role",
            session=None,
        )

        with (
            patch.object(
                IAMRoleManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                IAMRoleManager,
                "get",
                autospec=True,
                return_value=role,
            ) as get,
        ):
            related = job.role

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {"RoleName": "service-role/bedrock-eval-role"}
        assert related is role

    def test_model_customization_job_role_relation(self):
        job = ModelCustomizationJob.model_construct(
            jobArn="job-arn",
            jobName="customization-job",
            status="Completed",
            baseModelArn="arn:aws:bedrock:us-west-2::foundation-model/base",
            creationTime=datetime.now(tz=timezone.utc),
            roleArn="arn:aws:iam::123456789012:role/service-role/bedrock-customize-role",
            session=None,
        )
        role = IAMRole.model_construct(
            RoleName="service-role/bedrock-customize-role",
            Arn="arn:aws:iam::123456789012:role/service-role/bedrock-customize-role",
            session=None,
        )

        with (
            patch.object(
                IAMRoleManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                IAMRoleManager,
                "get",
                autospec=True,
                return_value=role,
            ) as get,
        ):
            related = job.role

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {
            "RoleName": "service-role/bedrock-customize-role"
        }
        assert related is role

    def test_model_invocation_job_role_relation(self):
        job = ModelInvocationJob.model_construct(
            jobArn="job-arn",
            roleArn="arn:aws:iam::123456789012:role/service-role/bedrock-invoke-role",
            submitTime=datetime.now(tz=timezone.utc),
            inputDataConfig={},
            outputDataConfig={},
            session=None,
        )
        role = IAMRole.model_construct(
            RoleName="service-role/bedrock-invoke-role",
            Arn="arn:aws:iam::123456789012:role/service-role/bedrock-invoke-role",
            session=None,
        )

        with (
            patch.object(
                IAMRoleManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                IAMRoleManager,
                "get",
                autospec=True,
                return_value=role,
            ) as get,
        ):
            related = job.role

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {"RoleName": "service-role/bedrock-invoke-role"}
        assert related is role

    def test_guardrail_kms_key_relation(self):
        guardrail = Guardrail.model_construct(
            guardrailId="gr-123",
            guardrailArn="guardrail-arn",
            guardrailName="Guardrail",
            kmsKeyArn="arn:aws:kms:us-west-2:123456789012:key/key-123",
            session=None,
        )
        kms_key = KMSKey.model_construct(
            KeyId="arn:aws:kms:us-west-2:123456789012:key/key-123",
            Arn="arn:aws:kms:us-west-2:123456789012:key/key-123",
            session=None,
        )

        with (
            patch.object(
                KMSKeyManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                KMSKeyManager,
                "get",
                autospec=True,
                return_value=kms_key,
            ) as get,
        ):
            related = guardrail.kms_key

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {
            "KeyId": "arn:aws:kms:us-west-2:123456789012:key/key-123"
        }
        assert related is kms_key

    def test_policy_build_workflows_relation(self):
        policy = AutomatedReasoningPolicy.model_construct(
            policyArn="policy-arn",
            policyName="Policy",
            version="1",
            policyId="policy-id",
            createdAt=datetime.now(tz=timezone.utc),
            updatedAt=datetime.now(tz=timezone.utc),
            session=None,
        )
        workflows = PrimaryBoto3ModelQuerySet(
            [
                AutomatedReasoningPolicyBuildWorkflow.model_construct(
                    policyArn="policy-arn",
                    buildWorkflowId="workflow-1",
                    session=None,
                )
            ]
        )

        with (
            patch.object(
                AutomatedReasoningPolicyBuildWorkflowManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                AutomatedReasoningPolicyBuildWorkflowManager,
                "list",
                autospec=True,
                return_value=workflows,
            ) as list_,
        ):
            related = policy.build_workflows

        using.assert_called_once()
        list_.assert_called_once()
        assert list_.call_args.kwargs == {"policyArn": "policy-arn"}
        assert related is workflows

    def test_policy_test_cases_relation(self):
        policy = AutomatedReasoningPolicy.model_construct(
            policyArn="policy-arn",
            policyName="Policy",
            version="1",
            policyId="policy-id",
            createdAt=datetime.now(tz=timezone.utc),
            updatedAt=datetime.now(tz=timezone.utc),
            session=None,
        )
        test_cases = PrimaryBoto3ModelQuerySet(
            [
                AutomatedReasoningPolicyTestCase.model_construct(
                    testCaseId="test-case-1",
                    session=None,
                )
            ]
        )

        with (
            patch.object(
                AutomatedReasoningPolicyTestCaseManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                AutomatedReasoningPolicyTestCaseManager,
                "list",
                autospec=True,
                return_value=test_cases,
            ) as list_,
        ):
            related = policy.test_cases

        using.assert_called_once()
        list_.assert_called_once()
        assert list_.call_args.kwargs == {"policyArn": "policy-arn"}
        assert related is test_cases

    def test_policy_helper_methods(self):
        policy = AutomatedReasoningPolicy.model_construct(
            policyArn="policy-arn",
            policyName="Policy",
            version="1",
            policyId="policy-id",
            createdAt=datetime.now(tz=timezone.utc),
            updatedAt=datetime.now(tz=timezone.utc),
            session=None,
        )
        test_results = PrimaryBoto3ModelQuerySet(
            [
                AutomatedReasoningPolicyTestResult.model_construct(
                    policyArn="policy-arn",
                    buildWorkflowId="workflow-1",
                    testCase="test-case-1",
                    session=None,
                )
            ]
        )
        next_scenario = AutomatedReasoningPolicyNextScenario.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            session=None,
        )
        assets = AutomatedReasoningPolicyBuildWorkflowResultAssets.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            session=None,
        )
        annotations = AutomatedReasoningPolicyAnnotations.model_construct(
            policyArn="policy-arn",
            buildWorkflowId="workflow-1",
            policyName="Policy",
            session=None,
        )

        with (
            patch.object(
                AutomatedReasoningPolicyTestResultManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as test_results_using,
            patch.object(
                AutomatedReasoningPolicyTestResultManager,
                "list",
                autospec=True,
                return_value=test_results,
            ) as list_results,
            patch.object(
                AutomatedReasoningPolicyNextScenarioManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as next_using,
            patch.object(
                AutomatedReasoningPolicyNextScenarioManager,
                "get",
                autospec=True,
                return_value=next_scenario,
            ) as get_next,
            patch.object(
                AutomatedReasoningPolicyBuildWorkflowResultAssetsManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as assets_using,
            patch.object(
                AutomatedReasoningPolicyBuildWorkflowResultAssetsManager,
                "get",
                autospec=True,
                return_value=assets,
            ) as get_assets,
            patch.object(
                AutomatedReasoningPolicyAnnotationsManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as annotations_using,
            patch.object(
                AutomatedReasoningPolicyAnnotationsManager,
                "get",
                autospec=True,
                return_value=annotations,
            ) as get_annotations,
        ):
            related_results = policy.test_results("workflow-1")
            related_next = policy.next_scenario("workflow-1")
            related_assets = policy.build_workflow_result_assets(
                "workflow-1", "POLICY"
            )
            related_annotations = policy.annotations("workflow-1")

        test_results_using.assert_called_once()
        list_results.assert_called_once()
        assert list_results.call_args.kwargs == {
            "policyArn": "policy-arn",
            "buildWorkflowId": "workflow-1",
        }
        next_using.assert_called_once()
        get_next.assert_called_once()
        assert get_next.call_args.kwargs == {
            "policyArn": "policy-arn",
            "buildWorkflowId": "workflow-1",
        }
        assets_using.assert_called_once()
        get_assets.assert_called_once()
        assert get_assets.call_args.kwargs == {
            "policyArn": "policy-arn",
            "buildWorkflowId": "workflow-1",
            "assetType": "POLICY",
        }
        annotations_using.assert_called_once()
        get_annotations.assert_called_once()
        assert get_annotations.call_args.kwargs == {
            "policyArn": "policy-arn",
            "buildWorkflowId": "workflow-1",
        }
        assert related_results is test_results
        assert related_next is next_scenario
        assert related_assets is assets
        assert related_annotations is annotations

    def test_model_customization_job_model_relations(self):
        job = ModelCustomizationJob.model_construct(
            jobArn="job-arn",
            jobName="customization-job",
            status="Completed",
            baseModelArn="arn:aws:bedrock:us-west-2::foundation-model/base",
            outputModelArn="arn:aws:bedrock:us-west-2:123456789012:custom-model/out",
            outputModelKmsKeyArn="arn:aws:kms:us-west-2:123456789012:key/output",
            creationTime=datetime.now(tz=timezone.utc),
            session=None,
        )
        foundation_model = FoundationModel.model_construct(
            modelId="arn:aws:bedrock:us-west-2::foundation-model/base",
            session=None,
        )
        custom_model = CustomModel.model_construct(
            modelArn="arn:aws:bedrock:us-west-2:123456789012:custom-model/out",
            session=None,
        )
        kms_key = KMSKey.model_construct(
            KeyId="arn:aws:kms:us-west-2:123456789012:key/output",
            Arn="arn:aws:kms:us-west-2:123456789012:key/output",
            session=None,
        )

        with (
            patch.object(
                FoundationModelManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as foundation_using,
            patch.object(
                FoundationModelManager,
                "get",
                autospec=True,
                return_value=foundation_model,
            ) as get_foundation,
            patch.object(
                CustomModelManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as custom_using,
            patch.object(
                CustomModelManager,
                "get",
                autospec=True,
                return_value=custom_model,
            ) as get_custom,
            patch.object(
                KMSKeyManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as kms_using,
            patch.object(
                KMSKeyManager,
                "get",
                autospec=True,
                return_value=kms_key,
            ) as get_kms,
        ):
            related_base_model = job.base_model
            related_output_model = job.output_model
            related_output_kms_key = job.output_model_kms_key

        foundation_using.assert_called_once()
        get_foundation.assert_called_once()
        assert get_foundation.call_args.kwargs == {
            "modelId": "arn:aws:bedrock:us-west-2::foundation-model/base"
        }
        custom_using.assert_called_once()
        get_custom.assert_called_once()
        assert get_custom.call_args.kwargs == {
            "modelArn": "arn:aws:bedrock:us-west-2:123456789012:custom-model/out"
        }
        kms_using.assert_called_once()
        get_kms.assert_called_once()
        assert get_kms.call_args.kwargs == {
            "KeyId": "arn:aws:kms:us-west-2:123456789012:key/output"
        }
        assert related_base_model is foundation_model
        assert related_output_model is custom_model
        assert related_output_kms_key is kms_key

    def test_model_customization_job_network_relations(self):
        job = ModelCustomizationJob.model_construct(
            jobArn="job-arn",
            jobName="customization-job",
            status="Completed",
            baseModelArn="arn:aws:bedrock:us-west-2::foundation-model/base",
            creationTime=datetime.now(tz=timezone.utc),
            vpcConfig=BedrockVpcConfig.model_construct(
                subnetIds=["subnet-1"],
                securityGroupIds=["sg-1"],
            ),
            session=None,
        )
        subnets = PrimaryBoto3ModelQuerySet(
            [Subnet.model_construct(SubnetId="subnet-1", session=None)]
        )
        security_groups = PrimaryBoto3ModelQuerySet(
            [SecurityGroup.model_construct(GroupId="sg-1", GroupName="sg", session=None)]
        )

        with (
            patch.object(
                SubnetManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as subnet_using,
            patch.object(
                SubnetManager,
                "list",
                autospec=True,
                return_value=subnets,
            ) as list_subnets,
            patch.object(
                SecurityGroupManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as sg_using,
            patch.object(
                SecurityGroupManager,
                "list",
                autospec=True,
                return_value=security_groups,
            ) as list_security_groups,
        ):
            related_subnets = job.subnets
            related_security_groups = job.security_groups

        subnet_using.assert_called_once()
        list_subnets.assert_called_once()
        assert list_subnets.call_args.kwargs == {"SubnetIds": ["subnet-1"]}
        sg_using.assert_called_once()
        list_security_groups.assert_called_once()
        assert list_security_groups.call_args.kwargs == {"GroupIds": ["sg-1"]}
        assert related_subnets is subnets
        assert related_security_groups is security_groups

    def test_model_invocation_job_relations(self):
        job = ModelInvocationJob.model_construct(
            jobArn="job-arn",
            roleArn="arn:aws:iam::123456789012:role/service-role/bedrock-invoke-role",
            modelId="arn:aws:bedrock:us-west-2::foundation-model/base",
            submitTime=datetime.now(tz=timezone.utc),
            inputDataConfig={},
            outputDataConfig={},
            vpcConfig=BedrockVpcConfig.model_construct(
                subnetIds=["subnet-1"],
                securityGroupIds=["sg-1"],
            ),
            session=None,
        )
        foundation_model = FoundationModel.model_construct(
            modelId="arn:aws:bedrock:us-west-2::foundation-model/base",
            session=None,
        )
        subnets = PrimaryBoto3ModelQuerySet(
            [Subnet.model_construct(SubnetId="subnet-1", session=None)]
        )
        security_groups = PrimaryBoto3ModelQuerySet(
            [SecurityGroup.model_construct(GroupId="sg-1", GroupName="sg", session=None)]
        )

        with (
            patch.object(
                FoundationModelManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as foundation_using,
            patch.object(
                FoundationModelManager,
                "get",
                autospec=True,
                return_value=foundation_model,
            ) as get_foundation,
            patch.object(
                SubnetManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as subnet_using,
            patch.object(
                SubnetManager,
                "list",
                autospec=True,
                return_value=subnets,
            ) as list_subnets,
            patch.object(
                SecurityGroupManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as sg_using,
            patch.object(
                SecurityGroupManager,
                "list",
                autospec=True,
                return_value=security_groups,
            ) as list_security_groups,
        ):
            related_model = job.foundation_model
            related_subnets = job.subnets
            related_security_groups = job.security_groups

        foundation_using.assert_called_once()
        get_foundation.assert_called_once()
        assert get_foundation.call_args.kwargs == {
            "modelId": "arn:aws:bedrock:us-west-2::foundation-model/base"
        }
        subnet_using.assert_called_once()
        list_subnets.assert_called_once()
        assert list_subnets.call_args.kwargs == {"SubnetIds": ["subnet-1"]}
        sg_using.assert_called_once()
        list_security_groups.assert_called_once()
        assert list_security_groups.call_args.kwargs == {"GroupIds": ["sg-1"]}
        assert related_model is foundation_model
        assert related_subnets is subnets
        assert related_security_groups is security_groups

    def test_enforced_guardrails_guardrail_relation(self):
        config = EnforcedGuardrailsConfiguration.model_construct(
            configId="config-1",
            guardrailArn="guardrail-arn",
            guardrailId="gr-123",
            session=None,
        )
        guardrail = Guardrail.model_construct(
            guardrailId="gr-123",
            guardrailArn="guardrail-arn",
            guardrailName="Guardrail",
            session=None,
        )

        with (
            patch.object(
                GuardrailManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                GuardrailManager,
                "get",
                autospec=True,
                return_value=guardrail,
            ) as get,
        ):
            related = config.guardrail

        using.assert_called_once()
        get.assert_called_once()
        assert get.call_args.kwargs == {"guardrailId": "gr-123"}
        assert related is guardrail

    def test_inference_profile_model_objects(self):
        profile = InferenceProfile.model_construct(
            inferenceProfileArn="profile-arn",
            inferenceProfileName="Profile",
            inferenceProfileId="profile-id",
            status="ACTIVE",
            type="APPLICATION",
            models=[
                InferenceProfileModel.model_construct(
                    modelArn="arn:aws:bedrock:us-west-2::foundation-model/base"
                ),
                InferenceProfileModel.model_construct(
                    modelArn="arn:aws:bedrock:us-west-2:123456789012:custom-model/out"
                ),
            ],
            session=None,
        )
        foundation_model = FoundationModel.model_construct(
            modelId="arn:aws:bedrock:us-west-2::foundation-model/base",
            session=None,
        )
        custom_model = CustomModel.model_construct(
            modelArn="arn:aws:bedrock:us-west-2:123456789012:custom-model/out",
            session=None,
        )

        with (
            patch.object(
                FoundationModelManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as foundation_using,
            patch.object(
                FoundationModelManager,
                "get",
                autospec=True,
                return_value=foundation_model,
            ) as get_foundation,
            patch.object(
                CustomModelManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as custom_using,
            patch.object(
                CustomModelManager,
                "get",
                autospec=True,
                return_value=custom_model,
            ) as get_custom,
        ):
            related = profile.model_objects

        foundation_using.assert_called_once()
        get_foundation.assert_called_once()
        custom_using.assert_called_once()
        get_custom.assert_called_once()
        assert related == [foundation_model, custom_model]

    def test_prompt_router_relations_and_model_objects(self):
        router = PromptRouter.model_construct(
            promptRouterArn="router-arn",
            promptRouterName="Router",
            routingCriteria={},
            models=[
                PromptRouterTargetModel.model_construct(
                    modelArn="arn:aws:bedrock:us-west-2::foundation-model/base"
                )
            ],
            fallbackModel=PromptRouterTargetModel.model_construct(
                modelArn="arn:aws:bedrock:us-west-2::foundation-model/fallback"
            ),
            status="AVAILABLE",
            type="custom",
            session=None,
        )
        fallback_model = FoundationModel.model_construct(
            modelId="arn:aws:bedrock:us-west-2::foundation-model/fallback",
            session=None,
        )
        listed_model = FoundationModel.model_construct(
            modelId="arn:aws:bedrock:us-west-2::foundation-model/base",
            session=None,
        )

        with (
            patch.object(
                FoundationModelManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as using,
            patch.object(
                FoundationModelManager,
                "get",
                autospec=True,
                side_effect=[fallback_model, listed_model],
            ) as get,
        ):
            related_fallback = router.fallback_model
            related_models = router.model_objects

        assert using.call_count == 2
        assert get.call_args_list[0].kwargs == {
            "modelId": "arn:aws:bedrock:us-west-2::foundation-model/fallback"
        }
        assert get.call_args_list[1].kwargs == {
            "modelId": "arn:aws:bedrock:us-west-2::foundation-model/base"
        }
        assert related_fallback is fallback_model
        assert related_models == [listed_model]

    def test_logging_configuration_related_resources(self):
        config = ModelInvocationLoggingConfiguration.model_construct(
            singletonId="account",
            cloudWatchConfig={"logGroupName": "bedrock-logs"},
            s3Config={"bucketName": "bedrock-bucket"},
            session=None,
        )
        log_group = LogGroup.model_construct(
            Arn="log-group-arn",
            logGroupName="bedrock-logs",
            session=None,
        )
        bucket = Bucket.model_construct(
            BucketName="bedrock-bucket",
            Region="us-west-2",
            CreationDate=datetime.now(tz=timezone.utc),
            session=None,
        )

        with (
            patch.object(
                LogGroupManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as log_using,
            patch.object(
                LogGroupManager,
                "get",
                autospec=True,
                return_value=log_group,
            ) as get_log_group,
            patch.object(
                BucketManager,
                "using",
                autospec=True,
                side_effect=lambda self, _session: self,
            ) as bucket_using,
            patch.object(
                BucketManager,
                "get",
                autospec=True,
                return_value=bucket,
            ) as get_bucket,
        ):
            related_log_group = config.log_group
            related_bucket = config.bucket

        log_using.assert_called_once()
        get_log_group.assert_called_once()
        assert get_log_group.call_args.kwargs == {"logGroupIdentifier": "bedrock-logs"}
        bucket_using.assert_called_once()
        get_bucket.assert_called_once()
        assert get_bucket.call_args.kwargs == {"BucketName": "bedrock-bucket"}
        assert related_log_group is log_group
        assert related_bucket is bucket

    def test_logging_configuration_related_resources_return_none_when_unset(self):
        config = ModelInvocationLoggingConfiguration.model_construct(
            singletonId="account",
            cloudWatchConfig={},
            s3Config={},
            session=None,
        )

        assert config.log_group is None
        assert config.bucket is None
