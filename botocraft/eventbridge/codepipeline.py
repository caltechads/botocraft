from typing import TYPE_CHECKING

from . import raw as raw_codepipeline
from .base import EventBridgeEvent
from .common import CloudTrailApiCallMixin, event_summary, first_resource

if TYPE_CHECKING:
    from botocraft.services.codepipeline import Pipeline, PipelineExecution


class CodePipelinePipelineExecutionStateChangeEvent(
    EventBridgeEvent,
    raw_codepipeline.CodepipelineCodePipelinePipelineExecutionStateChangeEvent,
):
    """
    EventBridge event for CodePipeline pipeline execution state changes.
    """

    def __str__(self) -> str:
        """
        Return readable string representation of event.

        Returns:
            Summary string for pipeline execution state transition.

        """
        return event_summary(
            "CodePipeline Pipeline Execution State Change",
            self,
            pipeline=self.detail.pipeline,
            state=self.detail.state,
            execution_id=self.detail.execution_id,
        )

    @property
    def pipeline_arn(self) -> str | None:
        """
        Return pipeline ARN carried by event resources list.

        Returns:
            Pipeline ARN when event names one resource, otherwise ``None``.

        """
        return first_resource(self.resources)

    @property
    def pipeline(self) -> "Pipeline | None":
        """
        Load pipeline referenced by event.

        Side Effects:
            Performs a ``GetPipeline`` request with attached boto3 session.

        Returns:
            Loaded pipeline model when available, otherwise ``None``.

        """
        from botocraft.services.codepipeline import Pipeline

        return Pipeline.objects.using(self.session).get(self.detail.pipeline)

    @property
    def pipeline_execution(self) -> "PipelineExecution | None":
        """
        Load pipeline execution referenced by event.

        Side Effects:
            Performs a ``GetPipelineExecution`` request with attached boto3
            session.

        Returns:
            Loaded pipeline execution when available, otherwise ``None``.

        """
        from botocraft.services.codepipeline import PipelineExecution

        return PipelineExecution.objects.using(self.session).get(
            self.detail.pipeline,
            self.detail.execution_id,
        )


class CodePipelineStageExecutionStateChangeEvent(
    EventBridgeEvent,
    raw_codepipeline.CodepipelineCodePipelineStageExecutionStateChangeEvent,
):
    """
    EventBridge event for CodePipeline stage execution state changes.
    """

    def __str__(self) -> str:
        """
        Return readable string representation of event.

        Returns:
            Summary string for stage execution state transition.

        """
        return event_summary(
            "CodePipeline Stage Execution State Change",
            self,
            pipeline=self.detail.pipeline,
            stage=self.detail.stage,
            state=self.detail.state,
            execution_id=self.detail.execution_id,
        )

    @property
    def pipeline_arn(self) -> str | None:
        """
        Return pipeline ARN carried by event resources list.

        Returns:
            Pipeline ARN when event names one resource, otherwise ``None``.

        """
        return first_resource(self.resources)

    @property
    def pipeline(self) -> "Pipeline | None":
        """
        Load pipeline referenced by event.

        Side Effects:
            Performs a ``GetPipeline`` request with attached boto3 session.

        Returns:
            Loaded pipeline model when available, otherwise ``None``.

        """
        from botocraft.services.codepipeline import Pipeline

        return Pipeline.objects.using(self.session).get(self.detail.pipeline)

    @property
    def pipeline_execution(self) -> "PipelineExecution | None":
        """
        Load pipeline execution referenced by event.

        Side Effects:
            Performs a ``GetPipelineExecution`` request with attached boto3
            session.

        Returns:
            Loaded pipeline execution when available, otherwise ``None``.

        """
        from botocraft.services.codepipeline import PipelineExecution

        return PipelineExecution.objects.using(self.session).get(
            self.detail.pipeline,
            self.detail.execution_id,
        )


class CodePipelineActionExecutionStateChangeEvent(
    EventBridgeEvent,
    raw_codepipeline.CodepipelineCodePipelineActionExecutionStateChangeEvent,
):
    """
    EventBridge event for CodePipeline action execution state changes.
    """

    def __str__(self) -> str:
        """
        Return readable string representation of event.

        Returns:
            Summary string for action execution state transition.

        """
        return event_summary(
            "CodePipeline Action Execution State Change",
            self,
            pipeline=self.detail.pipeline,
            stage=self.detail.stage,
            action=self.detail.action,
            state=self.detail.state,
            execution_id=self.detail.execution_id,
        )

    @property
    def pipeline_arn(self) -> str | None:
        """
        Return pipeline ARN carried by event resources list.

        Returns:
            Pipeline ARN when event names one resource, otherwise ``None``.

        """
        return first_resource(self.resources)

    @property
    def pipeline(self) -> "Pipeline | None":
        """
        Load pipeline referenced by event.

        Side Effects:
            Performs a ``GetPipeline`` request with attached boto3 session.

        Returns:
            Loaded pipeline model when available, otherwise ``None``.

        """
        from botocraft.services.codepipeline import Pipeline

        return Pipeline.objects.using(self.session).get(self.detail.pipeline)

    @property
    def pipeline_execution(self) -> "PipelineExecution | None":
        """
        Load pipeline execution referenced by event.

        Side Effects:
            Performs a ``GetPipelineExecution`` request with attached boto3
            session.

        Returns:
            Loaded pipeline execution when available, otherwise ``None``.

        """
        from botocraft.services.codepipeline import PipelineExecution

        return PipelineExecution.objects.using(self.session).get(
            self.detail.pipeline,
            self.detail.execution_id,
        )


class CodePipelineAWSAPICallViaCloudTrailEvent(
    CloudTrailApiCallMixin,
    EventBridgeEvent,
    raw_codepipeline.CodepipelineAWSAPICallViaCloudTrailEvent,
):
    """
    EventBridge event for CodePipeline API calls delivered via CloudTrail.
    """

    def __str__(self) -> str:
        """
        Return readable string representation of event.

        Returns:
            Summary string for the CloudTrail API call event.

        """
        return event_summary(
            "CodePipeline AWS API Call Via CloudTrail",
            self,
            event_source=self.detail.eventSource,
            api_call_name=self.detail.eventName,
        )

    @property
    def pipeline_arn(self) -> str | None:
        """
        Return pipeline ARN carried by event resources list.

        Returns:
            Pipeline ARN when event names one resource, otherwise ``None``.

        """
        return first_resource(self.resources)

    @property
    def pipeline(self) -> "Pipeline | None":
        """
        Load pipeline referenced by the event resource ARN.

        Side Effects:
            Performs a ``GetPipeline`` request with attached boto3 session when
            a pipeline ARN is present.

        Returns:
            Loaded pipeline model when event names a pipeline resource,
            otherwise ``None``.

        """
        from botocraft.services.codepipeline import Pipeline

        pipeline_arn = self.pipeline_arn
        if pipeline_arn is None:
            return None
        pipeline_name = pipeline_arn.rsplit(":", 1)[-1]
        return Pipeline.objects.using(self.session).get(pipeline_name)


#: Declarative mapping from EventBridge source/detail-type pairs to wrappers.
EVENT_CLASS_MAP = {
    (
        "aws.codepipeline",
        "CodePipeline Pipeline Execution State Change",
    ): CodePipelinePipelineExecutionStateChangeEvent,
    (
        "aws.codepipeline",
        "CodePipeline Stage Execution State Change",
    ): CodePipelineStageExecutionStateChangeEvent,
    (
        "aws.codepipeline",
        "CodePipeline Action Execution State Change",
    ): CodePipelineActionExecutionStateChangeEvent,
    (
        "aws.codepipeline",
        "AWS API Call via CloudTrail",
    ): CodePipelineAWSAPICallViaCloudTrailEvent,
}
