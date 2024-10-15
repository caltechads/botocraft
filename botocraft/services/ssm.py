# This file is automatically generated by botocraft.  Do not edit directly.
# pylint: disable=anomalous-backslash-in-string,unsubscriptable-object,line-too-long,arguments-differ,arguments-renamed,unused-import,redefined-outer-name
# pyright: reportUnusedImport=false
# mypy: disable-error-code="index, override, assignment, union-attr, misc"
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Literal, Optional, Type, cast

from pydantic import Field

from botocraft.mixins.tags import TagsDictMixin
from botocraft.services.common import Tag

from .abstract import (Boto3Model, Boto3ModelManager, PrimaryBoto3Model,
                       ReadonlyBoto3Model, ReadonlyBoto3ModelManager,
                       ReadonlyPrimaryBoto3Model)

# ===============
# Managers
# ===============


class ParameterManager(Boto3ModelManager):

    service_name: str = "ssm"

    def create(
        self,
        model: "Parameter",
        Description: Optional[str] = None,
        KeyId: Optional[str] = None,
        AllowedPattern: Optional[str] = None,
        Tags: Optional[List[Tag]] = None,
        Tier: Optional[Literal["Standard", "Advanced", "Intelligent-Tiering"]] = None,
        Policies: Optional[str] = None,
    ) -> int:
        """
        Add a parameter to the system.

        Args:
            model: The :py:class:``Parameter`` to create.

        Keyword Args:
            Description: Information about the parameter that you want to add to the
                system. Optional but recommended.
            KeyId: The Key Management Service (KMS) ID that you want to use to encrypt
                a parameter. Use a custom key for better security. Required for parameters
                that use the ``SecureString`` data type.
            AllowedPattern: A regular expression used to validate the parameter value.
                For example, for String types with values restricted to numbers, you can
                specify the following: AllowedPattern=^d+$
            Tags: Optional metadata that you assign to a resource. Tags enable you to
                categorize a resource in different ways, such as by purpose, owner, or
                environment. For example, you might want to tag a Systems Manager parameter
                to identify the type of resource to which it applies, the environment, or
                the type of configuration data referenced by the parameter. In this case,
                you could specify the following key-value pairs:
            Tier: The parameter tier to assign to a parameter.
            Policies: One or more policies to apply to a parameter. This operation
                takes a JSON array. Parameter Store, a capability of Amazon Web Services
                Systems Manager supports the following policy types:
        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        args = dict(
            Name=data.get("Name"),
            Value=data.get("Value"),
            Description=self.serialize(Description),
            Type=data.get("Type"),
            KeyId=self.serialize(KeyId),
            Overwrite=data.get("Overwrite"),
            AllowedPattern=self.serialize(AllowedPattern),
            Tags=self.serialize(Tags),
            Tier=self.serialize(Tier),
            Policies=self.serialize(Policies),
            DataType=data.get("DataType"),
        )
        _response = self.client.put_parameter(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = PutParameterResult(**_response)

        self.sessionize(response.Version)
        return cast(int, response.Version)

    def update(
        self,
        model: "Parameter",
        Description: Optional[str] = None,
        KeyId: Optional[str] = None,
        Overwrite: Optional[bool] = None,
        AllowedPattern: Optional[str] = None,
        Tags: Optional[List[Tag]] = None,
        Tier: Optional[Literal["Standard", "Advanced", "Intelligent-Tiering"]] = None,
        Policies: Optional[str] = None,
    ) -> int:
        """
        Add a parameter to the system.

        Args:
            model: The :py:class:``Parameter`` to update.

        Keyword Args:
            Description: Information about the parameter that you want to add to the
                system. Optional but recommended.
            KeyId: The Key Management Service (KMS) ID that you want to use to encrypt
                a parameter. Use a custom key for better security. Required for parameters
                that use the ``SecureString`` data type.
            Overwrite: Overwrite an existing parameter. The default value is ``false``.
            AllowedPattern: A regular expression used to validate the parameter value.
                For example, for String types with values restricted to numbers, you can
                specify the following: AllowedPattern=^d+$
            Tags: Optional metadata that you assign to a resource. Tags enable you to
                categorize a resource in different ways, such as by purpose, owner, or
                environment. For example, you might want to tag a Systems Manager parameter
                to identify the type of resource to which it applies, the environment, or
                the type of configuration data referenced by the parameter. In this case,
                you could specify the following key-value pairs:
            Tier: The parameter tier to assign to a parameter.
            Policies: One or more policies to apply to a parameter. This operation
                takes a JSON array. Parameter Store, a capability of Amazon Web Services
                Systems Manager supports the following policy types:
        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        args = dict(
            Name=data.get("Name"),
            Value=data.get("Value"),
            Description=self.serialize(Description),
            Type=data.get("Type"),
            KeyId=self.serialize(KeyId),
            Overwrite=self.serialize(Overwrite),
            AllowedPattern=self.serialize(AllowedPattern),
            Tags=self.serialize(Tags),
            Tier=self.serialize(Tier),
            Policies=self.serialize(Policies),
            DataType=data.get("DataType"),
        )
        _response = self.client.put_parameter(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = PutParameterResult(**_response)

        self.sessionize(response.Version)
        return cast(int, response.Version)

    def get(self, Name: str, *, WithDecryption: bool = True) -> Optional["Parameter"]:
        """
        Get information about one or more parameters by specifying multiple
        parameter names.

        Args:
            Name: The name of the parameter you want to query.

        Keyword Args:
            WithDecryption: Return decrypted secure string value. Return decrypted
                values for secure string parameters. This flag is ignored for ``String``
                and ``StringList`` parameter types.
        """
        args: Dict[str, Any] = dict(
            Names=self.serialize([Name]), WithDecryption=self.serialize(WithDecryption)
        )
        _response = self.client.get_parameters(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = GetParametersResult(**_response)

        if response and response.Parameters:
            self.sessionize(response.Parameters[0])
            return response.Parameters[0]
        return None

    def get_many(
        self, Names: List[str], *, WithDecryption: bool = True
    ) -> List["Parameter"]:
        """
        Get information about one or more parameters by specifying multiple
        parameter names.

        Args:
            Names: The names or Amazon Resource Names (ARNs) of the parameters that you
                want to query. For parameters shared with you from another account, you
                must use the full ARNs.

        Keyword Args:
            WithDecryption: Return decrypted secure string value. Return decrypted
                values for secure string parameters. This flag is ignored for ``String``
                and ``StringList`` parameter types.
        """
        args: Dict[str, Any] = dict(
            Names=self.serialize(Names), WithDecryption=self.serialize(WithDecryption)
        )
        _response = self.client.get_parameters(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = GetParametersResult(**_response)

        self.sessionize(respsonse.Parameters)
        return response.Parametersj

    def list(
        self,
        *,
        Filters: Optional[List["ParametersFilter"]] = None,
        ParameterFilters: Optional[List["ParameterStringFilter"]] = None,
        Shared: Optional[bool] = None
    ) -> List["ParameterMetadata"]:
        """
        Lists the parameters in your Amazon Web Services account or the parameters
        shared with you when you enable the
        `Shared <https://docs.aws.amazon.com/systems-
        manager/latest/APIReference/API_DescribeParameters.html#systemsmanager-
        DescribeParameters-request-Shared>`_ option.

        Keyword Args:
            Filters: This data type is deprecated. Instead, use ``ParameterFilters``.
            ParameterFilters: Filters to limit the request results.
            Shared: Lists parameters that are shared with you.

        """
        paginator = self.client.get_paginator("describe_parameters")
        args: Dict[str, Any] = dict(
            Filters=self.serialize(Filters),
            ParameterFilters=self.serialize(ParameterFilters),
            Shared=self.serialize(Shared),
        )
        response_iterator = paginator.paginate(
            **{k: v for k, v in args.items() if v is not None}
        )
        results: List["ParameterMetadata"] = []
        for _response in response_iterator:
            response = DescribeParametersResult(**_response)
            if response.Parameters:
                results.extend(response.Parameters)
            else:
                break
        self.sessionize(results)
        return results

    def delete(self, Name: str) -> None:
        """
        Delete a parameter from the system. After deleting a parameter, wait
        for at least 30 seconds to create a parameter with the same name.

        Args:
            Name: The name of the parameter to delete.
        """
        args: Dict[str, Any] = dict(Name=self.serialize(Name))
        self.client.delete_parameter(**{k: v for k, v in args.items() if v is not None})


# ==============
# Service Models
# ==============


class Parameter(PrimaryBoto3Model):
    """
    An Amazon Web Services Systems Manager parameter in Parameter Store.
    """

    manager_class: ClassVar[Type[Boto3ModelManager]] = ParameterManager

    Name: str
    """
    The name of the parameter.
    """
    Value: Optional[str] = None
    """
    The parameter value.
    """
    Type: Literal["String", "StringList", "SecureString"]
    """
    The type of parameter.

    Valid values include the following: ``String``,
    ``StringList``, and ``SecureString``.
    """
    DataType: Optional[str] = "text"
    """
    The data type of the parameter, such as ``text`` or ``aws:ec2:image``.

    The
    default is ``text``.
    """
    Version: int = Field(default=None, frozen=True)
    """
    The parameter version.
    """
    Selector: str = Field(default=None, frozen=True)
    """
    Either the version number or the label used to retrieve the parameter
    value.

    Specify selectors by using one of the following formats:
    """
    SourceResult: str = Field(default=None, frozen=True)
    """
    Applies to parameters that reference information in other Amazon Web
    Services services.

    ``SourceResult`` is the raw result or response from the source.
    """
    LastModifiedDate: datetime = Field(default=None, frozen=True)
    """
    Date the parameter was last changed or updated and the parameter version
    was created.
    """
    ARN: str = Field(default=None, frozen=True)
    """
    The Amazon Resource Name (ARN) of the parameter.
    """

    @property
    def pk(self) -> Optional[str]:
        """
        Return the primary key of the model.   This is the value of the
        :py:attr:`Name` attribute.

        Returns:
            The primary key of the model instance.
        """
        return self.Name

    @property
    def arn(self) -> Optional[str]:
        """
        Return the ARN of the model.   This is the value of the :py:attr:`ARN`
        attribute.

        Returns:
            The ARN of the model instance.
        """
        return self.ARN

    @property
    def name(self) -> Optional[str]:
        """
        Return the name of the model.   This is the value of the
        :py:attr:`Name` attribute.

        Returns:
            The name of the model instance.
        """
        return self.Name


# =======================
# Request/Response Models
# =======================


class PutParameterResult(Boto3Model):
    Version: Optional[int] = None
    """
    The new version number of a parameter.

    If you edit a parameter value, Parameter Store automatically creates a new
    version and assigns this new version a unique ID. You can reference a
    parameter version ID in API operations or in Systems Manager documents (SSM
    documents). By default, if you don't specify a specific version, the system
    returns the latest parameter value when a parameter is called.
    """
    Tier: Optional[Literal["Standard", "Advanced", "Intelligent-Tiering"]] = None
    """
    The tier assigned to the parameter.
    """


class GetParametersResult(Boto3Model):
    Parameters: Optional[List["Parameter"]] = None
    """
    A list of details for a parameter.
    """
    InvalidParameters: Optional[List[str]] = None
    """
    A list of parameters that aren't formatted correctly or don't run during an
    execution.
    """


class ParametersFilter(Boto3Model):
    """
    This data type is deprecated.

    Instead, use ParameterStringFilter.
    """

    Key: Literal["Name", "Type", "KeyId"]
    """
    The name of the filter.
    """
    Values: List[str]
    """
    The filter values.
    """


class ParameterStringFilter(Boto3Model):
    """
    One or more filters.

    Use a filter to return a more specific list of results.
    """

    Key: str
    """
    The name of the filter.
    """
    Option: Optional[str] = None
    """
    For all filters used with DescribeParameters, valid options include
    ``Equals`` and ``BeginsWith``.

    The ``Name`` filter additionally supports the ``Contains``
    option. (Exception: For filters using the key ``Path``, valid options include
    ``Recursive`` and ``OneLevel``.)
    """
    Values: Optional[List[str]] = None
    """
    The value you want to search for.
    """


class ParameterInlinePolicy(Boto3Model):
    """
    One or more policies assigned to a parameter.
    """

    PolicyText: Optional[str] = None
    """
    The JSON text of the policy.
    """
    PolicyType: Optional[str] = None
    """
    The type of policy.

    Parameter Store, a capability of Amazon Web Services Systems Manager,
    supports the following policy types: Expiration, ExpirationNotification,
    and NoChangeNotification.
    """
    PolicyStatus: Optional[str] = None
    """
    The status of the policy.

    Policies report the following statuses: Pending (the
    policy hasn't been enforced or applied yet), Finished (the policy was applied),
    Failed (the policy wasn't applied), or InProgress (the policy is being applied
    now).
    """


class ParameterMetadata(Boto3Model):
    """
    Metadata includes information like the Amazon Resource Name (ARN) of the
    last user to update the parameter and the date and time the parameter was
    last used.
    """

    Name: Optional[str] = None
    """
    The parameter name.
    """
    ARN: Optional[str] = None
    """
    The (ARN) of the last user to update the parameter.
    """
    Type: Optional[Literal["String", "StringList", "SecureString"]] = None
    """
    The type of parameter.

    Valid parameter types include the following: ``String``,
    ``StringList``, and ``SecureString``.
    """
    KeyId: Optional[str] = None
    """
    The alias of the Key Management Service (KMS) key used to encrypt the
    parameter.

    Applies to ``SecureString`` parameters only.
    """
    LastModifiedDate: Optional[datetime] = None
    """
    Date the parameter was last changed or updated.
    """
    LastModifiedUser: Optional[str] = None
    """
    Amazon Resource Name (ARN) of the Amazon Web Services user who last changed
    the parameter.
    """
    Description: Optional[str] = None
    """
    Description of the parameter actions.
    """
    AllowedPattern: Optional[str] = None
    """
    A parameter name can include only the following letters and symbols.
    """
    Version: Optional[int] = None
    """
    The parameter version.
    """
    Tier: Optional[Literal["Standard", "Advanced", "Intelligent-Tiering"]] = None
    """
    The parameter tier.
    """
    Policies: Optional[List["ParameterInlinePolicy"]] = None
    """
    A list of policies associated with a parameter.
    """
    DataType: Optional[str] = None
    """
    The data type of the parameter, such as ``text`` or ``aws:ec2:image``.

    The
    default is ``text``.
    """


class DescribeParametersResult(Boto3Model):
    Parameters: Optional[List["ParameterMetadata"]] = None
    """
    Parameters returned by the request.
    """
    NextToken: Optional[str] = None
    """
    The token to use when requesting the next set of items.
    """


class DeleteParameterResult(Boto3Model):
    pass
