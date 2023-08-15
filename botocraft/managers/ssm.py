from typing import List, Literal, Optional, cast

import boto3
from botocraft.models import (
    Boto3Model,
    ParametersFilter,
    Parameter,
    ParameterStringFilter,
    Tag,
)


class PutParameterResult(Boto3Model):
    #: The new version number of a parameter. If you edit a parameter value, Parameter
    #: Store automatically creates a new version and assigns this new version a unique
    #: ID. You can reference a parameter version ID in API operations or in Systems
    #: Manager documents (SSM documents). By default, if you don't specify a specific
    #: version, the system returns the latest parameter value when a parameter is
    #: called.
    Version: Optional[int] = None
    #: The tier assigned to the parameter.
    Tier: Optional[Literal["Standard", "Advanced", "Intelligent-Tiering"]] = None


class GetParametersResult(Boto3Model):
    #: A list of details for a parameter.
    Parameters: Optional[List[Parameter]] = None
    #: A list of parameters that aren't formatted correctly or don't run during an
    #: execution.
    InvalidParameters: Optional[List[str]] = None


class ParameterInlinePolicy(Boto3Model):
    """
    One or more policies assigned to a parameter.
    """

    #: The JSON text of the policy.
    PolicyText: Optional[str] = None
    #: The type of policy. Parameter Store, a capability of Amazon Web Services
    #: Systems Manager, supports the following policy types: Expiration,
    #: ExpirationNotification, and NoChangeNotification.
    PolicyType: Optional[str] = None
    #: The status of the policy. Policies report the following statuses: Pending (the
    #: policy hasn't been enforced or applied yet), Finished (the policy was applied),
    #: Failed (the policy wasn't applied), or InProgress (the policy is being applied
    #: now).
    PolicyStatus: Optional[str] = None


class ParameterMetadata(Boto3Model):
    """
    Metadata includes information like the ARN of the last user and the
    date/time the parameter was last used.
    """

    #: The parameter name.
    Name: Optional[str] = None
    #: The type of parameter. Valid parameter types include the following: ``String``,
    #: ``StringList``, and ``SecureString``.
    Type: Optional[Literal["String", "StringList", "SecureString"]] = None
    #: The ID of the query key used for this parameter.
    KeyId: Optional[str] = None
    #: Amazon Resource Name (ARN) of the Amazon Web Services user who last changed the
    #: parameter.
    LastModifiedUser: Optional[str] = None
    #: Description of the parameter actions.
    Description: Optional[str] = None
    #: A parameter name can include only the following letters and symbols.
    AllowedPattern: Optional[str] = None
    #: The parameter version.
    Version: Optional[int] = None
    #: The parameter tier.
    Tier: Optional[Literal["Standard", "Advanced", "Intelligent-Tiering"]] = None
    #: A list of policies associated with a parameter.
    Policies: Optional[List[ParameterInlinePolicy]] = None
    #: The data type of the parameter, such as ``text`` or ``aws:ec2:image``. The
    #: default is ``text``.
    DataType: Optional[str] = None


class DescribeParametersResult(Boto3Model):
    #: Parameters returned by the request.
    Parameters: Optional[List[ParameterMetadata]] = None
    #: The token to use when requesting the next set of items.
    NextToken: Optional[str] = None


class DeleteParameterResult(Boto3Model):
    pass


class ParameterManager:
    service_name: str = "ssm"

    def __init__(self) -> None:
        #: The boto3 client for the AWS service
        self.client = boto3.client(self.service_name)  # type: ignore

    def create(
        self,
        model: Parameter,
        Description: str = None,
        AllowedPattern: str = None,
        Tags: List[Tag] = None,
        Tier: Literal["Standard", "Advanced", "Intelligent-Tiering"] = None,
        Policies: str = None,
        Overwrite: bool = False,
        KeyId: str = None,
    ) -> int:
        data = model.model_dump()
        _response = self.client.put_parameter(
            Name=data["Name"],
            Value=data["Value"],
            Description=Description,
            Type=data["Type"],
            KeyId=KeyId,
            Overwrite=Overwrite,
            AllowedPattern=AllowedPattern,
            Tags=Tags,
            Tier=Tier,
            Policies=Policies,
            DataType=data["DataType"],
        )
        response = PutParameterResult(**_response)
        return cast(int, response.Version)

    def update(
        self,
        model: Parameter,
        Description: str = None,
        AllowedPattern: str = None,
        Tags: List[Tag] = None,
        Tier: Literal["Standard", "Advanced", "Intelligent-Tiering"] = None,
        Policies: str = None,
        Overwrite: bool = True,
        KeyId: str = None,
    ) -> "int":
        data = model.model_dump()
        _response = self.client.put_parameter(
            Name=data["Name"],
            Value=data["Value"],
            Description=Description,
            Type=data["Type"],
            KeyId=KeyId,
            Overwrite=Overwrite,
            AllowedPattern=AllowedPattern,
            Tags=Tags,
            Tier=Tier,
            Policies=Policies,
            DataType=data["DataType"],
        )
        response = PutParameterResult(**_response)
        return cast("int", response.Version)

    def get(
        self, Names: List[str], *, WithDecryption: bool = None
    ) -> Optional[Parameter]:
        _response = self.client.get_parameters(
            Names=Names, WithDecryption=WithDecryption
        )
        response = GetParametersResult(**_response)
        if response.Parameters:
            return response.Parameters[0]  # type: ignore # pylint: disable=unsubscriptable-object
        return None

    def list(
        self,
        *,
        Filters: List[ParametersFilter] = None,
        ParameterFilters: List[ParameterStringFilter] = None,
        MaxResults: int = None,
        NextToken: str = None
    ) -> List[ParameterMetadata]:
        _response = self.client.describe_parameters(
            Filters=Filters,
            ParameterFilters=ParameterFilters,
            MaxResults=MaxResults,
            NextToken=NextToken,
        )
        response = DescribeParametersResult(**_response)
        return response.Parameters

    def delete(self, Name: str) -> None:
        self.client.delete_parameter(Name=Name)
