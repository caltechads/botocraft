from functools import wraps
from typing import TYPE_CHECKING, Callable

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.acm import ACMCertificate


def certificates_only(
    func: Callable[..., list["ACMCertificate"]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.acm.ACMCertificateManager.list` to return a
    :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.acm.ACMCertificate` objects instead of only a list of
    ARNs.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        cert_summaries = func(self, *args, **kwargs)
        arns = [cert_summary.CertificateArn for cert_summary in cert_summaries]
        certs = []
        # We have to do this in batches of 50 because the get_many method,
        # which uses the boto3 ``describe_log_groups`` method, only accepts 50 ARNs
        # at a time.
        for arn in arns:
            certs.extend(self.get(arn))
        return PrimaryBoto3ModelQuerySet(certs)

    return wrapper


def certifictate_only(
    func: Callable[..., "ACMCertificate"],
) -> Callable[..., "ACMCertificate"]:
    """
    Wraps
    :py:meth:`botocraft.services.acm.ACMCertificateManager.import_certificate`
    to return the actual :py:class:`botocraft.services.acm.ACMCertificate` object
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "ACMCertificate":
        # import_certificate returns the ARN of the certificate
        cert_arn = func(self, *args, **kwargs)
        return self.get(cert_arn)

    return wrapper


def add_certificate_tags(
    func: Callable[..., "ACMCertificate"],
) -> Callable[..., "ACMCertificate"]:
    """
    Wraps :py:meth:`botocraft.services.acm.ACMCertificateManager.get` to add the
    tags to the :py:class:`ACMCertificate` object.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "ACMCertificate":
        certificate = func(self, *args, **kwargs)
        response = self.client.list_tags_for_certificate(
            CertificateArn=certificate.CertificateArn,
        )
        certificate.Tags = response["Tags"]
        return certificate

    return wrapper


class ACMManagerMixin:
    """
    Mixin for the :py:class:`ACMCertificateManager` class.
    """

    def update(self, model: "ACMCertificate") -> None:
        """
        Replace the tags on a certificate with the tags on ``model``.

        ACM has no operation that edits tags in place, so every existing tag is
        removed and then the tags on ``model`` are added.

        Args:
            model: the :py:class:`ACMCertificate` to update.

        """
        client = self.client  # type: ignore[attr-defined]
        existing = client.list_tags_for_certificate(
            CertificateArn=model.CertificateArn,
        )["Tags"]
        # ACM rejects an empty ``Tags`` list, so only call it when there is work.
        if existing:
            client.remove_tags_from_certificate(
                CertificateArn=model.CertificateArn,
                Tags=existing,
            )
        # boto3 wants plain dicts, not our Tag models.
        desired = [tag.model_dump(exclude_none=True) for tag in model.Tags or []]
        if desired:
            client.add_tags_to_certificate(
                CertificateArn=model.CertificateArn,
                Tags=desired,
            )
