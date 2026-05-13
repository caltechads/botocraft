from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from botocraft.services.bedrock import ResourcePolicy


class ResourcePolicyManagerMixin:
    """
    Bedrock resource policy helpers that assemble bespoke model instances.
    """

    def get(self, resourceArn: str) -> "ResourcePolicy | None":  # noqa: N803
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
