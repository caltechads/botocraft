from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
    from botocraft.services.bedrock import (
        AutomatedReasoningPolicyAnnotations,
        AutomatedReasoningPolicyBuildWorkflowResultAssets,
        AutomatedReasoningPolicyNextScenario,
        CustomModel,
        FoundationModel,
        ResourcePolicy,
    )
    from botocraft.services.logs import LogGroup
    from botocraft.services.s3 import Bucket


def _get_nested_value(container: Any, key: str) -> Any | None:
    """
    Read a nested value from either a dict-like object or model instance.

    Args:
        container: Mapping or object that may contain the nested value.
        key: Nested field name to read.

    Returns:
        Nested value when present, otherwise ``None``.

    """
    if container is None:
        return None
    if isinstance(container, dict):
        return container.get(key)
    return getattr(container, key, None)


def _resolve_model_arn(
    model_arn: str | None,
    session: Any,
) -> FoundationModel | CustomModel | None:
    """
    Resolve a Bedrock model ARN to a FoundationModel or CustomModel.

    Args:
        model_arn: Model ARN to resolve.
        session: Active boto3 session bound to the current model instance.

    Returns:
        Resolved foundation or custom model when recognizable, otherwise ``None``.

    """
    if not model_arn:
        return None
    from botocraft.services import CustomModel, FoundationModel

    if ":custom-model/" in model_arn:
        return CustomModel.objects.using(session).get(modelArn=model_arn)
    return FoundationModel.objects.using(session).get(modelId=model_arn)


class ResourcePolicyManagerMixin:
    """
    Bedrock resource policy helpers that assemble bespoke model instances.
    """

    def get(self: Any, resourceArn: str) -> ResourcePolicy | None:  # noqa: N803
        """
        Get resource policy document for a Bedrock resource.

        Args:
            resourceArn: The ARN of the Bedrock resource to which this resource
                policy applies.

        Returns:
            The assembled resource policy model when present, otherwise ``None``.

        """
        from botocraft.services import ResourcePolicy

        response = self.client.get_resource_policy(resourceArn=resourceArn)  # type: ignore[attr-defined]
        resource_policy = response.get("resourcePolicy")
        if resource_policy is None:
            return None
        model = ResourcePolicy(
            resourceArn=resourceArn,
            resourcePolicy=resource_policy,
        )
        model.set_session(self.session)  # type: ignore[attr-defined]
        return model


class AutomatedReasoningPolicyModelMixin:
    """
    Convenience methods for policy-linked Bedrock resources that need extra keys.
    """

    def test_results(
        self: Any,
        buildWorkflowId: str,  # noqa: N803
    ) -> PrimaryBoto3ModelQuerySet:
        """
        Return policy test results for a specific build workflow.

        Args:
            buildWorkflowId: Build workflow identifier to scope the test results.

        Returns:
            QuerySet of test results for the policy and build workflow.

        """
        from botocraft.services import AutomatedReasoningPolicyTestResult

        return AutomatedReasoningPolicyTestResult.objects.using(self.session).list(
            policyArn=self.policyArn,
            buildWorkflowId=buildWorkflowId,
        )

    def next_scenario(
        self: Any,
        buildWorkflowId: str,  # noqa: N803
    ) -> AutomatedReasoningPolicyNextScenario | None:
        """
        Return the next scenario for a specific build workflow.

        Args:
            buildWorkflowId: Build workflow identifier to scope the next scenario.

        Returns:
            Next scenario for the policy and build workflow, when present.

        """
        from botocraft.services import AutomatedReasoningPolicyNextScenario

        return AutomatedReasoningPolicyNextScenario.objects.using(self.session).get(
            policyArn=self.policyArn,
            buildWorkflowId=buildWorkflowId,
        )

    def build_workflow_result_assets(
        self: Any,
        buildWorkflowId: str,  # noqa: N803
        assetType: str,  # noqa: N803
    ) -> AutomatedReasoningPolicyBuildWorkflowResultAssets | None:
        """
        Return build workflow result assets for a specific workflow and asset type.

        Args:
            buildWorkflowId: Build workflow identifier to scope the assets.
            assetType: Asset type to retrieve.

        Returns:
            Build workflow result assets for the requested workflow and asset type.

        """
        from botocraft.services import AutomatedReasoningPolicyBuildWorkflowResultAssets

        return AutomatedReasoningPolicyBuildWorkflowResultAssets.objects.using(
            self.session
        ).get(
            policyArn=self.policyArn,
            buildWorkflowId=buildWorkflowId,
            assetType=assetType,
        )

    def annotations(
        self: Any,
        buildWorkflowId: str,  # noqa: N803
    ) -> AutomatedReasoningPolicyAnnotations | None:
        """
        Return annotations for a specific build workflow.

        Args:
            buildWorkflowId: Build workflow identifier to scope the annotations.

        Returns:
            Annotations for the policy and build workflow, when present.

        """
        from botocraft.services import AutomatedReasoningPolicyAnnotations

        return AutomatedReasoningPolicyAnnotations.objects.using(self.session).get(
            policyArn=self.policyArn,
            buildWorkflowId=buildWorkflowId,
        )


class InferenceProfileModelMixin:
    """
    Resolve the model references attached to an inference profile.
    """

    @cached_property
    def model_objects(self: Any) -> list[FoundationModel | CustomModel]:
        """
        Resolve all model references on the inference profile.

        Returns:
            Resolved foundation or custom models with recognized ARNs.

        """
        objects: list[FoundationModel | CustomModel] = []
        for model in self.models:
            resolved = _resolve_model_arn(model.modelArn, self.session)
            if resolved is not None:
                objects.append(resolved)
        return objects


class PromptRouterModelMixin:
    """
    Resolve the model references attached to a prompt router.
    """

    @cached_property
    def model_objects(self: Any) -> list[FoundationModel]:
        """
        Resolve all target foundation models on the prompt router.

        Returns:
            Resolved foundation models with recognized ARNs.

        """
        from botocraft.services import FoundationModel

        return [
            FoundationModel.objects.using(self.session).get(modelId=model.modelArn)
            for model in self.models
            if model.modelArn
        ]


class ModelInvocationLoggingConfigurationModelMixin:
    """
    Resolve optional CloudWatch Logs and S3 targets from logging configuration.
    """

    @cached_property
    def log_group(self: Any) -> LogGroup | None:
        """
        Return the CloudWatch log group configured for model invocation logging.

        Returns:
            Log group when configured, otherwise ``None``.

        """
        log_group_name = _get_nested_value(self.cloudWatchConfig, "logGroupName")
        if log_group_name is None:
            return None
        from botocraft.services import LogGroup

        return LogGroup.objects.using(self.session).get(
            logGroupIdentifier=log_group_name
        )

    @cached_property
    def bucket(self: Any) -> Bucket | None:
        """
        Return the S3 bucket configured for model invocation logging.

        Returns:
            Bucket when configured, otherwise ``None``.

        """
        bucket_name = _get_nested_value(self.s3Config, "bucketName")
        if bucket_name is None:
            return None
        from botocraft.services import Bucket

        return Bucket.objects.using(self.session).get(BucketName=bucket_name)
