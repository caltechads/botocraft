from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional

from typing_extensions import Literal

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services import (
        Bucket,
        BucketLoggingConfiguration,
        GetBucketLifecycleConfigurationOutput,
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


def object_get_add_tags(
    func: Callable[..., "S3Object"],
) -> Callable[..., "S3Object"]:
    """
    Wraps a boto3 method that returns an object to add the tags to the object.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "S3Object":
        from botocraft.services import S3Object

        bucket_name = args[0]

        obj = func(self, *args, **kwargs)
        if obj:
            obj.Tags = S3Object.objects.get_tags(Bucket=bucket_name, Key=obj.Key)
        obj.BucketName = bucket_name
        return obj

    return wrapper


def object_list_add_bucket_name_and_tags(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps a boto3 method that returns a list of objects to add the bucket name
    and tags to the objects.
    """

    @wraps(func)
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services import S3Object

        bucket_name = kwargs.get("Bucket")
        extras = kwargs.get("Include", [])
        qs = func(self, *args, **kwargs)
        for obj in qs.results:
            obj.BucketName = bucket_name  # type: ignore[attr-defined]
            if "TAGS" in extras:
                obj.Tags = S3Object.objects.get_tags(Bucket=obj.BucketName, Key=obj.Key)  # type: ignore[attr-defined]
        return qs

    return wrapper


def object_update_add_tags(
    func: Callable[..., "S3Object"],
) -> Callable[..., "S3Object"]:
    """
    Wraps a boto3 method that returns an object to add the tags to the object.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "S3Object":
        from botocraft.services import S3Object

        bucket_name = kwargs.get("Bucket")

        obj = func(self, *args, **kwargs)
        if obj:
            obj.Tags = S3Object.objects.put_tags(
                Bucket=bucket_name, Key=obj.Key, Tags=obj.Tags
            )
            obj.Tags = S3Object.objects.get_tags(Bucket=bucket_name, Key=obj.Key)
        obj.BucketName = bucket_name
        return obj

    return wrapper


def bucket_update_safe_get_lifecycle(
    func: Callable[..., "GetBucketLifecycleConfigurationOutput"],
) -> Callable[..., Optional["GetBucketLifecycleConfigurationOutput"]]:
    """
    Wraps a boto3 method that returns an object to add the lifecycle to the object.
    """

    @wraps(func)
    def wrapper(
        self, *args, **kwargs
    ) -> Optional["GetBucketLifecycleConfigurationOutput"]:
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

    def _get_bucket_logging_configuration(
        self, bucket_name: str
    ) -> Optional["BucketLoggingConfiguration"]:
        """
        Get the logging configuration for a bucket.
        """
        from botocraft.services import (
            BucketLoggingConfiguration,
            S3Grantee,
            S3PartitionedPrefix,
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
                            DisplayName=grantee.get("DisplayName"),
                            EmailAddress=grantee["EmailAddress"],
                            Type=grantee["Type"],
                            ID=grantee["ID"],
                            URI=grantee.get("URI"),
                        ),
                        Permission=grantee["Permission"],
                    )
                    for grantee in logging_configuration["LoggingEnabled"][
                        "TargetGrants"
                    ]
                ]
            if "TargetObjectKeyFormat" in logging_configuration["LoggingEnabled"]:
                object_key_format = S3TargetObjectKeyFormat(
                    SimplePrefix=logging_configuration["LoggingEnabled"][
                        "TargetObjectKeyFormat"
                    ]["SimplePrefix"],
                    PartitionedPrefix=S3PartitionedPrefix(
                        PartitionDateSource=logging_configuration["LoggingEnabled"][
                            "TargetObjectKeyFormat"
                        ]["PartitionedPrefix"]["PartitionDateSource"],
                    ),
                )
            _logging = BucketLoggingConfiguration(
                TargetBucket=logging_configuration["LoggingEnabled"]["TargetBucket"],
                TargetPrefix=logging_configuration["LoggingEnabled"]["TargetPrefix"],
                TargetGrants=target_grants,
                TargetObjectKeyFormat=object_key_format,
            )
        return _logging

    def _get_cors_rules(self, bucket_name: str) -> list["S3CORSRule"] | None:
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
            botocore.exceptions.ClientError: If the bucket does not exist or if
              there is an error retrieving it.

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
            raise self.DoesNotExist(msg)  # type: ignore[attr-defined]
        tags = self.objects.get_for_bucket(BucketName=BucketName)  # type: ignore[attr-defined]
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
        _region = model.Region if model.Region else region
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
