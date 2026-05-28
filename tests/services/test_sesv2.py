from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.sesv2 import (
    BulkEmailEntryResult,
    ConfigurationSet,
    ConfigurationSetManager,
    ContactList,
    ContactListManager,
    DedicatedIpPool,
    DedicatedIpPoolManager,
    DeliverabilityTestReport,
    DeliverabilityTestReportManager,
    EmailIdentity,
    EmailIdentityManager,
    EmailTemplate,
    EmailTemplateManager,
    MultiRegionEndpoint,
    MultiRegionEndpointManager,
    SESV2BulkEmailContent,
    SESV2BulkEmailEntry,
    SESV2Destination,
    SESV2EmailContent,
    SESV2ListManagementOptions,
    SESV2MessageTag,
)


class FakePaginator:
    """Minimal paginator stub matching boto3 paginator protocol."""

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses

    def paginate(self, **_: object) -> list[dict[str, object]]:
        return self.responses


def _email_identity_payload(identity: str) -> dict[str, object]:
    return {
        "IdentityType": "DOMAIN",
        "VerificationStatus": "SUCCESS",
        "VerifiedForSendingStatus": True,
        "DkimAttributes": {"Status": "SUCCESS", "SigningEnabled": True},
        "Tags": [{"Key": "env", "Value": "test"}],
        "EmailIdentity": identity,
    }


def _configuration_set_payload(name: str) -> dict[str, object]:
    return {
        "ConfigurationSetName": name,
        "Tags": [{"Key": "env", "Value": "test"}],
        "SendingOptions": {"SendingEnabled": True},
    }


def _contact_list_payload(name: str) -> dict[str, object]:
    now = datetime(2026, 5, 28, tzinfo=UTC)
    return {
        "ContactListName": name,
        "Description": "marketing list",
        "Topics": [
            {
                "TopicName": "news",
                "DisplayName": "Newsletter",
                "DefaultSubscriptionStatus": "OPT_IN",
            }
        ],
        "CreatedTimestamp": now,
        "LastUpdatedTimestamp": now,
        "Tags": [{"Key": "team", "Value": "growth"}],
    }


def _email_template_payload(name: str) -> dict[str, object]:
    return {
        "TemplateName": name,
        "TemplateContent": {
            "Subject": "hello",
            "Text": "plain",
            "Html": "<p>plain</p>",
        },
        "Tags": [{"Key": "env", "Value": "test"}],
    }


def _dedicated_ip_pool_payload(name: str) -> dict[str, object]:
    return {
        "PoolName": name,
        "ScalingMode": "STANDARD",
    }


def _multi_region_endpoint_payload(name: str) -> dict[str, object]:
    now = datetime(2026, 5, 28, tzinfo=UTC)
    return {
        "EndpointName": name,
        "EndpointId": "mre-123",
        "Routes": [{"Region": "us-east-1"}, {"Region": "us-west-2"}],
        "Status": "READY",
        "CreatedTimestamp": now,
        "LastUpdatedTimestamp": now,
    }


def _deliverability_test_report_response(report_id: str) -> dict[str, object]:
    now = datetime(2026, 5, 28, tzinfo=UTC)
    return {
        "DeliverabilityTestReport": {
            "ReportId": report_id,
            "ReportName": "smoke",
            "Subject": "hello",
            "FromEmailAddress": "sender@example.com",
            "CreateDate": now,
            "DeliverabilityTestStatus": "COMPLETED",
        },
        "OverallPlacement": {
            "InboxPercentage": 99.0,
            "SpamPercentage": 1.0,
            "MissingPercentage": 0.0,
            "SpfPercentage": 100.0,
            "DkimPercentage": 100.0,
        },
        "IspPlacements": [],
        "Message": "done",
        "Tags": [{"Key": "env", "Value": "test"}],
    }


class TestEmailIdentityManager:
    @patch("boto3.client")
    def test_get_email_identity_injects_requested_identifier(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_email_identity.return_value = {
            key: value
            for key, value in _email_identity_payload("example.com").items()
            if key != "EmailIdentity"
        }
        mock_boto3_client.return_value = mock_client

        manager = EmailIdentityManager()
        identity = manager.get("example.com")

        mock_client.get_email_identity.assert_called_once_with(
            EmailIdentity="example.com",
        )
        assert isinstance(identity, EmailIdentity)
        assert identity.EmailIdentity == "example.com"
        assert identity.VerificationStatus == "SUCCESS"

    @patch("boto3.client")
    def test_list_email_identities_returns_public_models(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.list_email_identities.return_value = {
            "EmailIdentities": [
                {
                    "IdentityType": "DOMAIN",
                    "IdentityName": "example.com",
                    "SendingEnabled": True,
                    "VerificationStatus": "SUCCESS",
                }
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = EmailIdentityManager()
        identities = manager.list()

        mock_client.list_email_identities.assert_called_once_with()
        assert isinstance(identities, PrimaryBoto3ModelQuerySet)
        assert len(identities) == 1
        assert isinstance(identities[0], EmailIdentity)
        assert identities[0].EmailIdentity == "example.com"
        assert identities[0].SendingEnabled is True

    @patch("boto3.client")
    def test_send_email_returns_message_id(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "msg-123"}
        mock_boto3_client.return_value = mock_client

        manager = EmailIdentityManager()
        content = SESV2EmailContent(
            Simple={
                "Subject": {"Data": "hello"},
                "Body": {"Text": {"Data": "plain body"}},
            }
        )
        destination = SESV2Destination(ToAddresses=["to@example.com"])
        tags = [SESV2MessageTag(Name="campaign", Value="spring")]
        list_management = SESV2ListManagementOptions(
            ContactListName="marketing",
            TopicName="news",
        )

        message_id = manager.send(
            "sender@example.com",
            content,
            Destination=destination,
            ConfigurationSetName="transactional",
            EmailTags=tags,
            ListManagementOptions=list_management,
        )

        mock_client.send_email.assert_called_once_with(
            FromEmailAddress="sender@example.com",
            Content=content.model_dump(exclude_none=True, by_alias=True),
            Destination=destination.model_dump(exclude_none=True, by_alias=True),
            ConfigurationSetName="transactional",
            EmailTags=[tag.model_dump(exclude_none=True, by_alias=True) for tag in tags],
            ListManagementOptions=list_management.model_dump(
                exclude_none=True,
                by_alias=True,
            ),
        )
        assert message_id == "msg-123"

    @patch("boto3.client")
    def test_model_send_binds_identity(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_boto3_client.return_value = MagicMock()
        identity = EmailIdentity(IdentityName="sender@example.com")
        identity.set_session(None)

        content = SESV2EmailContent(
            Template={
                "TemplateName": "welcome",
                "TemplateData": "{}",
            }
        )

        with patch.object(
            EmailIdentityManager,
            "send",
            return_value="msg-456",
        ) as mock_send:
            message_id = identity.send(content, TenantName="tenant-a")

        mock_send.assert_called_once_with(
            "sender@example.com",
            content,
            Destination=None,
            ReplyToAddresses=None,
            FeedbackForwardingEmailAddress=None,
            FeedbackForwardingEmailAddressIdentityArn=None,
            FromEmailAddressIdentityArn=None,
            EmailTags=None,
            ConfigurationSetName=None,
            ListManagementOptions=None,
            EndpointId=None,
            TenantName="tenant-a",
        )
        assert message_id == "msg-456"

    @patch("boto3.client")
    def test_send_bulk_returns_entry_results(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.send_bulk_email.return_value = {
            "BulkEmailEntryResults": [
                {"Status": "SUCCESS", "MessageId": "bulk-1"},
                {"Status": "SUCCESS", "MessageId": "bulk-2"},
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = EmailIdentityManager()
        default_content = SESV2BulkEmailContent(
            Template={
                "TemplateName": "newsletter",
                "TemplateData": "{}",
            }
        )
        entries = [
            SESV2BulkEmailEntry(
                Destination={"ToAddresses": ["one@example.com"]},
                ReplacementEmailContent={
                    "ReplacementTemplate": {"ReplacementTemplateData": '{"name":"One"}'}
                },
            ),
            SESV2BulkEmailEntry(
                Destination={"ToAddresses": ["two@example.com"]},
            ),
        ]
        default_tags = [SESV2MessageTag(Name="campaign", Value="bulk")]

        results = manager.send_bulk(
            "sender@example.com",
            default_content,
            entries,
            DefaultEmailTags=default_tags,
            TenantName="tenant-a",
        )

        mock_client.send_bulk_email.assert_called_once_with(
            FromEmailAddress="sender@example.com",
            DefaultContent=default_content.model_dump(exclude_none=True, by_alias=True),
            BulkEmailEntries=[
                entry.model_dump(exclude_none=True, by_alias=True) for entry in entries
            ],
            DefaultEmailTags=[
                tag.model_dump(exclude_none=True, by_alias=True) for tag in default_tags
            ],
            TenantName="tenant-a",
        )
        assert [result.MessageId for result in results] == ["bulk-1", "bulk-2"]
        assert all(isinstance(result, BulkEmailEntryResult) for result in results)

    @patch("boto3.client")
    def test_model_send_bulk_binds_identity(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_boto3_client.return_value = MagicMock()
        identity = EmailIdentity(IdentityName="sender@example.com")
        identity.set_session(None)
        default_content = SESV2BulkEmailContent(
            Template={"TemplateName": "bulk-template", "TemplateData": "{}"}
        )
        entries = [
            SESV2BulkEmailEntry(Destination={"ToAddresses": ["person@example.com"]})
        ]
        expected = [BulkEmailEntryResult(Status="SUCCESS", MessageId="bulk-999")]

        with patch.object(
            EmailIdentityManager,
            "send_bulk",
            return_value=expected,
        ) as mock_send_bulk:
            results = identity.send_bulk(
                default_content,
                entries,
                ConfigurationSetName="transactional",
            )

        mock_send_bulk.assert_called_once_with(
            "sender@example.com",
            default_content,
            entries,
            ReplyToAddresses=None,
            FeedbackForwardingEmailAddress=None,
            FeedbackForwardingEmailAddressIdentityArn=None,
            FromEmailAddressIdentityArn=None,
            DefaultEmailTags=None,
            ConfigurationSetName="transactional",
            EndpointId=None,
            TenantName=None,
        )
        assert results == expected


class TestConfigurationSetManager:
    @patch("boto3.client")
    def test_list_configuration_sets_hydrates_names(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.list_configuration_sets.return_value = {
            "ConfigurationSets": ["transactional"]
        }
        mock_client.get_configuration_set.return_value = _configuration_set_payload(
            "transactional"
        )
        mock_boto3_client.return_value = mock_client

        manager = ConfigurationSetManager()
        configuration_sets = manager.list()

        mock_client.list_configuration_sets.assert_called_once_with()
        mock_client.get_configuration_set.assert_called_once_with(
            ConfigurationSetName="transactional"
        )
        assert isinstance(configuration_sets, PrimaryBoto3ModelQuerySet)
        assert len(configuration_sets) == 1
        assert isinstance(configuration_sets[0], ConfigurationSet)
        assert configuration_sets[0].ConfigurationSetName == "transactional"


class TestContactListManager:
    @patch("boto3.client")
    def test_create_contact_list_refreshes_model(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_contact_list.return_value = {}
        mock_client.get_contact_list.return_value = _contact_list_payload("marketing")
        mock_boto3_client.return_value = mock_client

        manager = ContactListManager()
        model = ContactList(
            ContactListName="marketing",
            Description="marketing list",
            Topics=[
                {
                    "TopicName": "news",
                    "DisplayName": "Newsletter",
                    "DefaultSubscriptionStatus": "OPT_IN",
                }
            ],
        )
        created = manager.create(model)

        mock_client.create_contact_list.assert_called_once()
        mock_client.get_contact_list.assert_called_once_with(
            ContactListName="marketing"
        )
        assert isinstance(created, ContactList)
        assert created.ContactListName == "marketing"


class TestEmailTemplateManager:
    @patch("boto3.client")
    def test_update_email_template_refreshes_model(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.update_email_template.return_value = {}
        mock_client.get_email_template.return_value = _email_template_payload("welcome")
        mock_boto3_client.return_value = mock_client

        manager = EmailTemplateManager()
        model = EmailTemplate(
            TemplateName="welcome",
            TemplateContent={
                "Subject": "hello",
                "Text": "plain",
                "Html": "<p>plain</p>",
            },
        )
        updated = manager.update(model)

        mock_client.update_email_template.assert_called_once()
        mock_client.get_email_template.assert_called_once_with(TemplateName="welcome")
        assert isinstance(updated, EmailTemplate)
        assert updated.TemplateName == "welcome"


class TestDedicatedIpPoolManager:
    @patch("boto3.client")
    def test_list_dedicated_ip_pools_hydrates_names(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.list_dedicated_ip_pools.return_value = {
            "DedicatedIpPools": ["pool-a"]
        }
        mock_client.get_dedicated_ip_pool.return_value = {
            "DedicatedIpPool": _dedicated_ip_pool_payload("pool-a")
        }
        mock_boto3_client.return_value = mock_client

        manager = DedicatedIpPoolManager()
        pools = manager.list()

        mock_client.list_dedicated_ip_pools.assert_called_once_with()
        mock_client.get_dedicated_ip_pool.assert_called_once_with(PoolName="pool-a")
        assert isinstance(pools, PrimaryBoto3ModelQuerySet)
        assert len(pools) == 1
        assert isinstance(pools[0], DedicatedIpPool)
        assert pools[0].PoolName == "pool-a"


class TestMultiRegionEndpointManager:
    @patch("boto3.client")
    def test_create_multi_region_endpoint_refreshes_model(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_multi_region_endpoint.return_value = {
            "EndpointId": "mre-123",
            "Status": "CREATING",
        }
        mock_client.get_multi_region_endpoint.return_value = (
            _multi_region_endpoint_payload("mail-endpoint")
        )
        mock_boto3_client.return_value = mock_client

        manager = MultiRegionEndpointManager()
        model = MultiRegionEndpoint(
            EndpointName="mail-endpoint",
            Details={"RoutesDetails": [{"Region": "us-east-1"}]},
        )
        created = manager.create(model)

        mock_client.create_multi_region_endpoint.assert_called_once()
        mock_client.get_multi_region_endpoint.assert_called_once_with(
            EndpointName="mail-endpoint"
        )
        assert isinstance(created, MultiRegionEndpoint)
        assert created.EndpointName == "mail-endpoint"
        assert created.Status == "READY"


class TestDeliverabilityTestReportManager:
    @patch("boto3.client")
    def test_create_deliverability_test_report_refreshes_model(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_deliverability_test_report.return_value = {
            "ReportId": "rpt-123",
            "DeliverabilityTestStatus": "IN_PROGRESS",
        }
        mock_client.get_deliverability_test_report.return_value = (
            _deliverability_test_report_response("rpt-123")
        )
        mock_boto3_client.return_value = mock_client

        manager = DeliverabilityTestReportManager()
        model = DeliverabilityTestReport(
            ReportName="smoke",
            FromEmailAddress="sender@example.com",
            Content={
                "Simple": {
                    "Subject": {"Data": "hello"},
                    "Body": {"Text": {"Data": "plain"}},
                }
            },
        )
        created = manager.create(model)

        mock_client.create_deliverability_test_report.assert_called_once()
        mock_client.get_deliverability_test_report.assert_called_once_with(
            ReportId="rpt-123"
        )
        assert isinstance(created, DeliverabilityTestReport)
        assert created.ReportId == "rpt-123"
        assert created.OverallPlacement is not None
        assert created.OverallPlacement.InboxPercentage == 99.0
