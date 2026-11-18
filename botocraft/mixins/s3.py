import gzip
import inspect
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

from typing_extensions import Literal

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services import (
        Bucket,
        BucketLoggingConfiguration,
        GetBucketLifecycleConfigurationOutput,
        GetObjectOutput,
        S3CORSRule,
        S3Object,
    )

# ----------
# Decorators
# ----------


def bucket_list_names_to_buckets(
    func: Callable[..., Any],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps a boto3 method that returns a list of S3 bucket names to return a list
    of :py:class:`Bucket` objects instead.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        self = args[0]
        buckets = func(*args, **kwargs)
        names = [bucket["Name"] for bucket in buckets]
        _buckets = [self.get(BucketName=name) for name in names]
        return PrimaryBoto3ModelQuerySet(buckets)

    return wrapper


def object_list_add_bucket_name_and_tags(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps a boto3 method that returns a list of objects to add the bucket name
    and tags to the objects.  ``Bucket`` may be passed positionally or by
    keyword.

    Args:
        func: The manager ``list`` method to wrap.

    Returns:
        The wrapped method.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services import S3Object

        arguments = inspect.signature(func).bind(self, *args, **kwargs).arguments
        bucket_name = arguments["Bucket"]
        extras = arguments.get("Include") or []
        qs = func(self, *args, **kwargs)
        for obj in qs.results:
            obj.BucketName = bucket_name  # type: ignore[attr-defined]
            if "TAGS" in extras:
                obj.Tags = S3Object.objects.get_tags(Bucket=obj.BucketName, Key=obj.Key)  # type: ignore[attr-defined]
        return qs

    return wrapper


def object_get_add_bucket_name_and_key(
    func: Callable[..., "S3Object | None"],
) -> Callable[..., "S3Object | None"]:
    """
    Wraps ``get_object`` to set ``BucketName`` and ``Key`` on the returned
    object, because the AWS response does not echo them.  ``Bucket`` and ``Key``
    may be passed positionally or by keyword.  The response ``Body`` is not
    kept; use :py:meth:`S3ObjectMixin.contents` to read it.

    Args:
        func: The manager ``get`` method to wrap.

    Returns:
        The wrapped method.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "S3Object | None":
        arguments = inspect.signature(func).bind(self, *args, **kwargs).arguments
        obj = func(self, *args, **kwargs)
        if obj is not None:
            obj.BucketName = arguments["Bucket"]
            obj.Key = arguments["Key"]
        return obj

    return wrapper


def object_create_return_model(
    func: Callable[..., Any],
) -> Callable[..., "S3Object"]:
    """
    Wraps ``put_object`` so that ``create`` returns the :py:class:`S3Object`
    that was passed in, with ``BucketName`` set from the ``Bucket`` argument.

    Args:
        func: The manager ``create`` method to wrap.

    Returns:
        The wrapped method.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "S3Object":
        bound = inspect.signature(func).bind(self, *args, **kwargs)
        model = bound.arguments["model"]
        if not model.ChecksumAlgorithm:
            # ``S3Object.ChecksumAlgorithm`` is the list-valued ListObjectsV2
            # field and defaults to ``[]``, but ``put_object`` wants a string,
            # so an empty value must not reach it.
            bound.arguments["model"] = model.model_copy(
                update={"ChecksumAlgorithm": None}
            )
        func(*bound.args, **bound.kwargs)
        model.BucketName = bound.arguments["Bucket"]
        self.sessionize(model)
        return model

    return wrapper


def bucket_update_safe_get_lifecycle(
    func: Callable[..., "GetBucketLifecycleConfigurationOutput"],
) -> Callable[..., "GetBucketLifecycleConfigurationOutput | None"]:
    """
    Wraps a boto3 method that returns an object to add the lifecycle to the object.
    """

    @wraps(func)
    def wrapper(
        self, *args, **kwargs
    ) -> "GetBucketLifecycleConfigurationOutput | None":
        try:
            lifecycle = func(self, *args, **kwargs)
        except self.client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
                return None
            raise
        return lifecycle

    return wrapper


# -------------
# Mixin Classes
# -------------


class BucketManagerMixin:
    """
    A mixin class that extends :py:class:`~botocraft.services.s3.BucketManager`
    to add the :py:meth:`get` method to retrieve a bucket by name.   Buckets     are
    not first class objects in the AWS API, so this is a convenience method to
    retrieve a bucket by name and return our bespoke
    :py:class:`~botocraft.service.s3.Bucket` object.
    """

    class DoesNotExist(Exception):
        """Raised when the requested bucket does not exist."""

    def _get_bucket_logging_configuration(
        self, bucket_name: str
    ) -> "BucketLoggingConfiguration | None":
        """
        Get the logging configuration for a bucket.
        """
        from botocraft.services import (
            BucketLoggingConfiguration,
            S3Grantee,
            S3PartitionedPrefix,
            S3SimplePrefix,
            S3TargetObjectKeyFormat,
            TargetGrant,
        )

        s3 = self.client  # type: ignore[attr-defined]
        logging_configuration = s3.get_bucket_logging(Bucket=bucket_name)
        _logging: BucketLoggingConfiguration | None = None
        target_grants: list[TargetGrant] | None = None
        object_key_format: S3TargetObjectKeyFormat | None = None
        if "LoggingEnabled" in logging_configuration:
            if "TargetGrants" in logging_configuration["LoggingEnabled"]:
                target_grants = [
                    TargetGrant(
                        Grantee=S3Grantee(
                            DisplayName=grant["Grantee"].get("DisplayName"),
                            EmailAddress=grant["Grantee"].get("EmailAddress"),
                            Type=grant["Grantee"]["Type"],
                            ID=grant["Grantee"].get("ID"),
                            URI=grant["Grantee"].get("URI"),
                        ),
                        Permission=grant["Permission"],
                    )
                    for grant in logging_configuration["LoggingEnabled"][
                        "TargetGrants"
                    ]
                ]
            if "TargetObjectKeyFormat" in logging_configuration["LoggingEnabled"]:
                fmt = logging_configuration["LoggingEnabled"]["TargetObjectKeyFormat"]
                # Only one of SimplePrefix / PartitionedPrefix is ever present.
                object_key_format = S3TargetObjectKeyFormat(
                    SimplePrefix=(
                        S3SimplePrefix() if "SimplePrefix" in fmt else None
                    ),
                    PartitionedPrefix=(
                        S3PartitionedPrefix(
                            PartitionDateSource=fmt["PartitionedPrefix"].get(
                                "PartitionDateSource"
                            ),
                        )
                        if "PartitionedPrefix" in fmt
                        else None
                    ),
                )
            _logging = BucketLoggingConfiguration(
                TargetBucket=logging_configuration["LoggingEnabled"]["TargetBucket"],
                TargetPrefix=logging_configuration["LoggingEnabled"]["TargetPrefix"],
                TargetGrants=target_grants,
                TargetObjectKeyFormat=object_key_format,
            )
        return _logging

    def _get_cors_rules(self, bucket_name: str) -> "list[S3CORSRule] | None":
        """
        Get the CORS rules for a bucket.

        Args:
            bucket_name: The name of the bucket to get the CORS rules for.

        Returns:
            A list of :py:class:`~botocraft.services.s3.S3CORSRule` objects.

        Raises:
            botocore.exceptions.ClientError: If there is an error retrieving the
                CORS rules.

        """
        from botocraft.services import S3CORSRule

        s3 = self.client  # type: ignore[attr-defined]
        # Get the bucket CORS rules
        _cors_rules = None
        try:
            cors_rules = s3.get_bucket_cors(Bucket=bucket_name)
        except s3.exceptions.ClientError as e:
            if "The CORS configuration does not exist" not in str(e):
                raise
        else:
            _cors_rules = [
                S3CORSRule(
                    Id=rule["ID"],
                    AllowedHeaders=rule["AllowedHeaders"],
                    AllowedMethods=rule["AllowedMethods"],
                    AllowedOrigins=rule["AllowedOrigins"],
                    ExposeHeaders=rule["ExposeHeaders"],
                    MaxAgeSeconds=rule["MaxAgeSeconds"],
                )
                for rule in cors_rules["CORSRules"]
            ]
        return _cors_rules

    def get(self, BucketName: str):  # noqa: N803
        """
        Get a bucket by name.

        Args:
            BucketName: The name of the bucket to retrieve.

        Raises:
            DoesNotExist: If the bucket does not exist.
            botocore.exceptions.ClientError: If there is an error retrieving it.

        Returns:
            An object representing the bucket, including its ARN,
              attributes, and tags.

        """
        from botocraft.services import Bucket

        s3 = self.client  # type: ignore[attr-defined]
        _bucket = s3.list_buckets(Prefix=BucketName)
        for bucket in _bucket["Buckets"]:
            if bucket["Name"] == BucketName:
                break
        else:
            msg = f"Bucket {BucketName} not found"
            raise self.DoesNotExist(msg)
        try:
            tags = self.get_tags(Bucket=BucketName)  # type: ignore[attr-defined]
        except s3.exceptions.ClientError as e:
            # A bucket with no tags raises NoSuchTagSet
            if "NoSuchTagSet" not in str(e):
                raise
            tags = []
        _logging = self._get_bucket_logging_configuration(BucketName)
        # Get the bucket versioning
        versioning = s3.get_bucket_versioning(Bucket=BucketName)
        # Get the bucket ownership controls
        _ownership_controls = None
        try:
            ownership_controls = s3.get_bucket_ownership_controls(Bucket=BucketName)
        except s3.exceptions.ClientError as e:
            if "The bucket ownership controls were not found" not in str(e):
                raise
        else:
            _ownership_controls = ownership_controls["Rules"][0]["ObjectOwnership"]
        # Get the bucket CORS rules
        _cors_rules = self._get_cors_rules(BucketName)

        _bucket = Bucket(
            BucketName=BucketName,
            BucketArn=bucket.get("BucketArn"),
            Region=bucket["BucketRegion"],
            CreationDate=bucket["CreationDate"],
            Tags=tags,
            LoggingConfiguration=_logging,
            VersioningEnabled=versioning["Status"] == "Enabled",
            MFADelete=versioning.get("MFADelete") == "Enabled",
            ObjectOwnership=_ownership_controls,
            CORSRules=_cors_rules,
        )
        _bucket.set_session(self.session)  # type: ignore[attr-defined]
        return _bucket

    def create(
        self,
        model: "Bucket",
        ACL: Literal[  # noqa: N803
            "private",
            "public-read",
            "public-read-write",
            "authenticated-read",
            "aws-exec-read",
            "bucket-owner-read",
            "bucket-owner-full-control",
        ]
        | None = "private",
        DataRedundancy: Literal[  # noqa: N803
            "SingleLocalZone",
            "SingleAvailabilityZone",
        ]
        | None = None,
        VersioningMFAIdentifier: str | None = None,  # noqa: N803
        ChecksumAlgorithm: Literal[  # noqa: N803
            "CRC32", "CRC32C", "SHA1", "SHA256", "CRC64NVME"
        ]
        | None = None,
    ) -> "Bucket":
        """
        Create a bucket.

        Args:
            model: The :py:class:`Bucket` to create.

        Keyword Args:
            ACL: The ACL for the bucket.
            DataRedundancy: The data redundancy for the bucket.
                "SingleLocalZone", "SingleAvailabilityZone".
            VersioningMFAIdentifier: The MFA identifier for the bucket versioning.
                Only used if ``model.VersioningEnabled`` is ``True``.
            ChecksumAlgorithm: The checksum algorithm for the request to the AWS API.
                When you supply this, there must be a corresponding checksum header
                in the request.

        Returns:
            The :py:class:`Bucket` that was created.

        """
        from botocraft.services import S3Tagging

        # Get the current region
        region = self.session.region_name  # type: ignore[attr-defined]
        _region = model.Region or region
        s3 = self.client  # type: ignore[attr-defined]
        create_bucket_configuration = {
            "LocationConstraint": _region,
            "Tags": self.serialize(model.Tags),  # type: ignore[attr-defined]
        }
        if DataRedundancy:
            create_bucket_configuration["Bucket"] = {}
            create_bucket_configuration["Bucket"]["DataRedundancy"] = DataRedundancy
        s3.create_bucket(
            ACL=ACL,
            Bucket=model.BucketName,
            CreateBucketConfiguration=create_bucket_configuration,
            ObjectOwnership=model.ObjectOwnership,
            CORSRules=self.serialize(model.CORSRules),  # type: ignore[attr-defined]
        )
        if model.LoggingConfiguration:
            s3.put_bucket_logging(
                Bucket=model.BucketName,
                LoggingConfiguration=self.serialize(model.LoggingConfiguration),  # type: ignore[attr-defined]
            )
        if model.VersioningEnabled:
            s3.put_bucket_versioning(
                Bucket=model.BucketName,
                MFA=VersioningMFAIdentifier,
                VersioningConfiguration={
                    "Status": "Enabled" if model.VersioningEnabled else "Suspended",
                    "MFADelete": "Enabled" if model.MFADelete else "Disabled",
                    "ChecksumAlgorithm": ChecksumAlgorithm,
                },
            )
        if model.CORSRules:
            s3.put_bucket_cors(
                Bucket=model.BucketName,
                CORSConfiguration=self.serialize(model.CORSRules),  # type: ignore[attr-defined]
                ChecksumAlgorithm=ChecksumAlgorithm,
            )
        if model.Tags:
            _tags = S3Tagging(TagSet=model.Tags)  # type: ignore[attr-defined]
            self.objects.put_tags(  # type: ignore[attr-defined]
                Bucket=model.BucketName,
                Tagging=_tags,
                ChecksumAlgorithm=ChecksumAlgorithm,
            )
        return self.get(BucketName=model.BucketName)

    def update(
        self,
        model: "Bucket",
        ACL: Literal[  # noqa: N803
            "private",
            "public-read",
            "public-read-write",
            "authenticated-read",
            "aws-exec-read",
            "bucket-owner-read",
            "bucket-owner-full-control",
        ]
        | None = None,
        ChecksumAlgorithm: Literal[  # noqa: N803
            "CRC32", "CRC32C", "SHA1", "SHA256", "CRC64NVME"
        ]
        | None = None,
        VersioningMFAIdentifier: str | None = None,  # noqa: N803
    ) -> "Bucket":
        """
        Update a bucket.
        """
        from botocraft.services import S3Tagging

        s3 = self.client  # type: ignore[attr-defined]

        if ACL:
            s3.put_bucket_acl(
                Bucket=model.BucketName,
                ACL=ACL,
                ChecksumAlgorithm=ChecksumAlgorithm,
            )
        if model.LoggingConfiguration:
            s3.put_bucket_logging(
                Bucket=model.BucketName,
                LoggingConfiguration=self.serialize(model.LoggingConfiguration),  # type: ignore[attr-defined]
            )
        if model.VersioningEnabled:
            response = s3.get_bucket_versioning(Bucket=model.BucketName)
            if (
                response["Status"] != model.VersioningEnabled
                or response["MFADelete"] != model.MFADelete
            ):
                if model.MFADelete and VersioningMFAIdentifier is None:
                    msg = "VersioningMFAIdentifier is required when MFADelete is True"
                    raise ValueError(msg)
                s3.put_bucket_versioning(
                    Bucket=model.BucketName,
                    MFA=VersioningMFAIdentifier,
                    Status="Enabled" if model.VersioningEnabled else "Suspended",
                    MFADelete="Enabled" if model.MFADelete else "Disabled",
                    ChecksumAlgorithm=ChecksumAlgorithm,
                )
        if model.CORSRules:
            s3.put_bucket_cors(
                Bucket=model.BucketName,
                CORSConfiguration=self.serialize(model.CORSRules),  # type: ignore[attr-defined]
                ChecksumAlgorithm=ChecksumAlgorithm,
            )
        if model.Tags:
            _tags = S3Tagging(TagSet=model.Tags)  # type: ignore[attr-defined]
            self.objects.put_tags(  # type: ignore[attr-defined]
                Bucket=model.BucketName,
                Tagging=_tags,
                ChecksumAlgorithm=ChecksumAlgorithm,
            )
        return self.get(BucketName=model.BucketName)

    def delete(self, model: "Bucket") -> None:
        """
        Delete a bucket.

        Args:
            model: The :py:class:`Bucket` to delete.

        """
        s3 = self.client  # type: ignore[attr-defined]
        if model.VersioningEnabled:
            s3.delete_bucket_versioning(Bucket=model.BucketName)
        if model.CORSRules:
            s3.delete_bucket_cors(Bucket=model.BucketName)
        if model.LoggingConfiguration:
            s3.delete_bucket_logging(Bucket=model.BucketName)
        if model.Tags:
            s3.delete_bucket_tagging(Bucket=model.BucketName)
        if model.ACL:
            s3.delete_bucket_acl(Bucket=model.BucketName)
        if model.ObjectOwnership:
            s3.delete_bucket_ownership_controls(Bucket=model.BucketName)
        s3.delete_bucket_policy(BucketName=model.BucketName)  # type: ignore[attr-defined]
        s3.delete_website(BucketName=model.BucketName)  # type: ignore[attr-defined]
        s3.delete_bucket_lifecycle(BucketName=model.BucketName)  # type: ignore[attr-defined]
        s3.delete_bucket(Bucket=model.BucketName)


class S3ObjectMixin:
    """
    Adds :py:meth:`contents` to :py:class:`~botocraft.services.s3.S3Object`.
    """

    def contents(self) -> "GetObjectOutput":
        """
        Retrieve this object from Amazon S3, with its ``Body`` as an unread
        :py:class:`botocore.response.StreamingBody`.  Each call issues a new
        ``get_object`` request.

        Raises:
            ValueError: If ``BucketName`` or ``Key`` is not set.

        Returns:
            The :py:class:`~botocraft.services.s3.GetObjectOutput`.

        """
        from botocraft.services import GetObjectOutput

        for field in ("BucketName", "Key"):
            if not getattr(self, field):
                msg = f"Cannot read contents: S3Object.{field} is not set"
                raise ValueError(msg)
        manager = self.objects.using(self.session)  # type: ignore[attr-defined]
        response = GetObjectOutput(
            **manager.client.get_object(Bucket=self.BucketName, Key=self.Key)  # type: ignore[attr-defined]
        )
        manager.sessionize(response)
        return response


class GetObjectOutputMixin:
    """
    Adds some convenience methods to the
    :py:class:`~botocraft.services.s3.GetObjectOutput` class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._body_cache: bytes | None = None

    @property
    def data(self) -> bytes:
        """
        Examine the :attr:`~botocraft.services.s3.GetObjectOutput.Body` of the
        and determine if it is a gzip file.  If it is, return the decompressed
        data.  If it is not, return the raw data.

        Cache the decompressed data in :attr:`_body_cache`.  This is done because
        the :attr:`~botocraft.services.s3.GetObjectOutput.Body` is a streaming
        body that can only be read once -- all further attempts to read the body will
        return ``b""``.

        Returns:
            The decompressed data.

        """
        if self._body_cache is not None:
            return self._body_cache
        if self.Body:  # type: ignore[attr-defined]
            body = self.Body.read()  # type: ignore[attr-defined]
            self._body_cache = body
            if body.startswith(b"gz"):
                self._body_cache = gzip.decompress(body)
            return self._body_cache
        return b""
