from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.ses import (
    SESBody,
    SESBulkEmailDestination,
    SESBulkEmailDestinationStatus,
    SESConfigurationSet,
    SESConfigurationSetManager,
    SESContent,
    SESCustomVerificationEmailTemplate,
    SESCustomVerificationEmailTemplateManager,
    SESDestination,
    SESIdentity,
    SESIdentityManager,
    SESMessage,
    SESRawMessage,
    SESReceiptFilter,
    SESReceiptFilterManager,
    SESReceiptRuleSet,
    SESReceiptRuleSetManager,
    SESTemplate,
    SESTemplateManager,
)


def _configuration_set_payload(name: str) -> dict[str, object]:
    return {
        "ConfigurationSet": {"Name": name},
        "EventDestinations": [
            {
                "Name": "events",
                "Enabled": True,
                "MatchingEventTypes": ["send", "delivery"],
            }
        ],
        "TrackingOptions": {"CustomRedirectDomain": "click.example.com"},
        "DeliveryOptions": {"TlsPolicy": "Require"},
        "ReputationOptions": {
            "SendingEnabled": True,
            "ReputationMetricsEnabled": True,
        },
    }


def _template_payload(name: str) -> dict[str, object]:
    return {
        "TemplateName": name,
        "SubjectPart": "hello",
        "TextPart": "plain",
        "HtmlPart": "<p>plain</p>",
    }


def _custom_verification_payload(name: str) -> dict[str, object]:
    return {
        "TemplateName": name,
        "FromEmailAddress": "sender@example.com",
        "TemplateSubject": "verify",
        "TemplateContent": "hello world",
        "SuccessRedirectionURL": "https://example.com/success",
        "FailureRedirectionURL": "https://example.com/failure",
    }


def _identity_verification_attributes_payload(
    identity: str,
    *,
    verification_status: str = "Success",
    verification_token: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {"VerificationStatus": verification_status}
    if verification_token is not None:
        payload["VerificationToken"] = verification_token
    return {
        "VerificationAttributes": {
            identity: payload,
        }
    }


def _receipt_rule_set_payload(name: str) -> dict[str, object]:
    now = datetime(2026, 5, 28, tzinfo=UTC)
    return {
        "Metadata": {
            "Name": name,
            "CreatedTimestamp": now,
        },
        "Rules": [
            {
                "Name": "store-mail",
                "Enabled": True,
                "TlsPolicy": "Optional",
                "Recipients": ["mail@example.com"],
            }
        ],
    }


class TestConfigurationSetManager:
    @patch("boto3.client")
    def test_get_configuration_set_flattens_nested_payload(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.describe_configuration_set.return_value = _configuration_set_payload(
            "transactional"
        )
        mock_boto3_client.return_value = mock_client

        manager = SESConfigurationSetManager()
        configuration_set = manager.get("transactional")

        mock_client.describe_configuration_set.assert_called_once_with(
            ConfigurationSetName="transactional"
        )
        assert isinstance(configuration_set, SESConfigurationSet)
        assert configuration_set.ConfigurationSetName == "transactional"
        assert configuration_set.TrackingOptions is not None
        assert configuration_set.EventDestinations is not None
        assert configuration_set.EventDestinations[0].EventDestinationName == "events"

    @patch("boto3.client")
    def test_create_configuration_set_refreshes_model(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_boto3_client.return_value = MagicMock()
        manager = SESConfigurationSetManager()
        model = SESConfigurationSet(Name="transactional")

        with patch.object(
            SESConfigurationSetManager,
            "get",
            return_value=model,
        ) as mock_get:
            refreshed = manager.create(model)

        mock_get.assert_called_once_with(name="transactional")
        assert refreshed is model


class TestTemplateManager:
    @patch("boto3.client")
    def test_list_templates_converts_metadata_to_public_models(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        now = datetime(2026, 5, 28, tzinfo=UTC)
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {
                "TemplatesMetadata": [
                    {
                        "Name": "welcome",
                        "CreatedTimestamp": now,
                    }
                ]
            }
        ]
        mock_client.get_paginator.return_value = paginator
        mock_boto3_client.return_value = mock_client

        manager = SESTemplateManager()
        templates = manager.list()

        mock_client.get_paginator.assert_called_once_with("list_templates")
        assert isinstance(templates, PrimaryBoto3ModelQuerySet)
        assert len(templates) == 1
        assert isinstance(templates[0], SESTemplate)
        assert templates[0].TemplateName == "welcome"
        assert templates[0].CreatedTimestamp == now

    @patch("boto3.client")
    def test_render_template_returns_rendered_template(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.test_render_template.return_value = {
            "RenderedTemplate": "Hello Ada"
        }
        mock_boto3_client.return_value = mock_client

        manager = SESTemplateManager()
        rendered = manager.render("welcome", '{"first_name": "Ada"}')

        mock_client.test_render_template.assert_called_once_with(
            TemplateName="welcome",
            TemplateData='{"first_name": "Ada"}',
        )
        assert rendered == "Hello Ada"

    @patch("boto3.client")
    def test_send_mail_binds_template_and_returns_message_id(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.send_templated_email.return_value = {"MessageId": "msg-123"}
        mock_boto3_client.return_value = mock_client

        manager = SESTemplateManager()

        message_id = manager.send_mail(
            "sender@example.com",
            {"ToAddresses": ["to@example.com"]},
            "welcome",
            '{"name":"Ada"}',
            ConfigurationSetName="transactional",
        )

        mock_client.send_templated_email.assert_called_once_with(
            Source="sender@example.com",
            Destination={"ToAddresses": ["to@example.com"]},
            Template="welcome",
            TemplateData='{"name":"Ada"}',
            ConfigurationSetName="transactional",
        )
        assert message_id == "msg-123"

    @patch("boto3.client")
    def test_model_send_mail_binds_template_name(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_boto3_client.return_value = MagicMock()
        template = SESTemplate(
            TemplateName="welcome",
            SubjectPart="hello",
            TextPart="plain",
            HtmlPart="<p>plain</p>",
        )
        template.set_session(None)

        with patch.object(SESTemplateManager, "send_mail", return_value="msg-456") as mock_send:
            destination = SESDestination(ToAddresses=["to@example.com"])
            message_id = template.send_mail(
                "sender@example.com",
                destination,
                '{"name":"Ada"}',
                ConfigurationSetName="transactional",
            )

        mock_send.assert_called_once_with(
            "sender@example.com",
            destination,
            "welcome",
            '{"name":"Ada"}',
            ReplyToAddresses=None,
            ReturnPath=None,
            SourceArn=None,
            ReturnPathArn=None,
            Tags=None,
            ConfigurationSetName="transactional",
        )
        assert message_id == "msg-456"

    @patch("boto3.client")
    def test_send_bulk_templated_mail_returns_status_models(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.send_bulk_templated_email.return_value = {
            "Status": [
                {"Status": "Success", "MessageId": "bulk-1"},
                {"Status": "MessageRejected", "Error": "bad address"},
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = SESTemplateManager()

        results = manager.send_bulk_templated_mail(
            "sender@example.com",
            "welcome",
            [
                {"Destination": {"ToAddresses": ["one@example.com"]}},
                {
                    "Destination": {"ToAddresses": ["two@example.com"]},
                    "ReplacementTemplateData": '{"name":"Two"}',
                },
            ],
            DefaultTemplateData='{"name":"Friend"}',
        )

        mock_client.send_bulk_templated_email.assert_called_once_with(
            Source="sender@example.com",
            Template="welcome",
            Destinations=[
                {"Destination": {"ToAddresses": ["one@example.com"]}},
                {
                    "Destination": {"ToAddresses": ["two@example.com"]},
                    "ReplacementTemplateData": '{"name":"Two"}',
                },
            ],
            DefaultTemplateData='{"name":"Friend"}',
        )
        assert [type(result) for result in results] == [SESBulkEmailDestinationStatus] * 2
        assert results[0].MessageId == "bulk-1"
        assert results[1].Error == "bad address"

    @patch("boto3.client")
    def test_model_send_bulk_templated_mail_binds_template_name(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_boto3_client.return_value = MagicMock()
        template = SESTemplate(
            TemplateName="welcome",
            SubjectPart="hello",
            TextPart="plain",
            HtmlPart="<p>plain</p>",
        )
        template.set_session(None)
        statuses = [SESBulkEmailDestinationStatus(Status="Success", MessageId="bulk-1")]

        with patch.object(
            SESTemplateManager,
            "send_bulk_templated_mail",
            return_value=statuses,
        ) as mock_send_bulk:
            destinations = [
                SESBulkEmailDestination(Destination={"ToAddresses": ["to@example.com"]})
            ]
            results = template.send_bulk_templated_mail(
                "sender@example.com",
                destinations,
            )

        mock_send_bulk.assert_called_once_with(
            "sender@example.com",
            "welcome",
            destinations,
            SourceArn=None,
            ReplyToAddresses=None,
            ReturnPath=None,
            ReturnPathArn=None,
            ConfigurationSetName=None,
            DefaultTags=None,
        )
        assert results is statuses


class TestCustomVerificationEmailTemplateManager:
    @patch("boto3.client")
    def test_get_custom_verification_template_returns_public_model(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_custom_verification_email_template.return_value = (
            _custom_verification_payload("verify-template")
        )
        mock_boto3_client.return_value = mock_client

        manager = SESCustomVerificationEmailTemplateManager()
        template = manager.get("verify-template")

        mock_client.get_custom_verification_email_template.assert_called_once_with(
            TemplateName="verify-template"
        )
        assert isinstance(template, SESCustomVerificationEmailTemplate)
        assert template.TemplateName == "verify-template"
        assert template.TemplateContent == "hello world"

    @patch("boto3.client")
    def test_send_verification_mail_returns_message_id(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.send_custom_verification_email.return_value = {
            "MessageId": "verify-123"
        }
        mock_boto3_client.return_value = mock_client

        manager = SESCustomVerificationEmailTemplateManager()
        message_id = manager.send_verification_mail(
            "person@example.com",
            "verify-template",
            ConfigurationSetName="transactional",
        )

        mock_client.send_custom_verification_email.assert_called_once_with(
            EmailAddress="person@example.com",
            TemplateName="verify-template",
            ConfigurationSetName="transactional",
        )
        assert message_id == "verify-123"

    @patch("boto3.client")
    def test_model_send_verification_mail_binds_template_name(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_boto3_client.return_value = MagicMock()
        template = SESCustomVerificationEmailTemplate(TemplateName="verify-template")
        template.set_session(None)

        with patch.object(
            SESCustomVerificationEmailTemplateManager,
            "send_verification_mail",
            return_value="verify-456",
        ) as mock_send:
            message_id = template.send_verification_mail(
                "person@example.com",
                ConfigurationSetName="transactional",
            )

        mock_send.assert_called_once_with(
            "person@example.com",
            "verify-template",
            ConfigurationSetName="transactional",
        )
        assert message_id == "verify-456"


class TestIdentityManager:
    @patch("boto3.client")
    def test_list_identities_returns_public_models(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"Identities": ["sender@example.com", "example.com"]}
        ]
        mock_client.get_paginator.return_value = paginator
        mock_boto3_client.return_value = mock_client

        manager = SESIdentityManager()
        identities = manager.list()

        mock_client.get_paginator.assert_called_once_with("list_identities")
        assert isinstance(identities, PrimaryBoto3ModelQuerySet)
        assert len(identities) == 2
        assert identities[0].Identity == "sender@example.com"
        assert identities[0].IdentityType == "EmailAddress"
        assert identities[1].IdentityType == "Domain"

    @patch("boto3.client")
    def test_get_identity_flattens_verification_attributes(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_identity_verification_attributes.return_value = (
            _identity_verification_attributes_payload(
                "example.com",
                verification_token="token-123",  # noqa: S106
            )
        )
        mock_boto3_client.return_value = mock_client

        manager = SESIdentityManager()
        identity = manager.get("example.com")

        mock_client.get_identity_verification_attributes.assert_called_once_with(
            Identities=["example.com"]
        )
        assert isinstance(identity, SESIdentity)
        assert identity.Identity == "example.com"
        assert identity.VerificationToken == "token-123"
        assert identity.IdentityType == "Domain"

    @patch("boto3.client")
    def test_create_email_identity_verifies_email_and_refreshes_model(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_boto3_client.return_value = MagicMock()
        manager = SESIdentityManager()
        model = SESIdentity(Identity="sender@example.com", IdentityType="EmailAddress")

        with patch.object(
            SESIdentityManager,
            "get",
            return_value=model,
        ) as mock_get:
            refreshed = manager.create(model)

        manager.client.verify_email_identity.assert_called_once_with(
            EmailAddress="sender@example.com"
        )
        mock_get.assert_called_once_with("sender@example.com")
        assert refreshed is model

    @patch("boto3.client")
    def test_create_domain_identity_preserves_verification_token(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.verify_domain_identity.return_value = {
            "VerificationToken": "token-123"
        }
        mock_boto3_client.return_value = mock_client
        manager = SESIdentityManager()
        refreshed = SESIdentity(Identity="example.com", IdentityType="Domain")

        with patch.object(
            SESIdentityManager,
            "get",
            return_value=refreshed,
        ) as mock_get:
            identity = manager.create(refreshed)

        mock_client.verify_domain_identity.assert_called_once_with(Domain="example.com")
        mock_get.assert_called_once_with("example.com")
        assert identity is not None
        assert identity.VerificationToken == "token-123"

    @patch("boto3.client")
    def test_send_mail_returns_message_id(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "msg-123"}
        mock_boto3_client.return_value = mock_client

        manager = SESIdentityManager()
        message_id = manager.send_mail(
            "sender@example.com",
            {"ToAddresses": ["to@example.com"]},
            {
                "Subject": {"Data": "hello"},
                "Body": {"Text": {"Data": "plain"}},
            },
            ConfigurationSetName="transactional",
            Tags=[{"Name": "campaign", "Value": "spring"}],
        )

        mock_client.send_email.assert_called_once_with(
            Source="sender@example.com",
            Destination={"ToAddresses": ["to@example.com"]},
            Message={
                "Subject": {"Data": "hello"},
                "Body": {"Text": {"Data": "plain"}},
            },
            ConfigurationSetName="transactional",
            Tags=[{"Name": "campaign", "Value": "spring"}],
        )
        assert message_id == "msg-123"

    @patch("boto3.client")
    def test_send_raw_mail_returns_message_id(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.send_raw_email.return_value = {"MessageId": "raw-123"}
        mock_boto3_client.return_value = mock_client

        manager = SESIdentityManager()
        message_id = manager.send_raw_mail(
            "sender@example.com",
            {"Data": b"raw-content"},
            Destinations=["to@example.com"],
        )

        mock_client.send_raw_email.assert_called_once_with(
            Source="sender@example.com",
            RawMessage={"Data": b"raw-content"},
            Destinations=["to@example.com"],
        )
        assert message_id == "raw-123"

    @patch("boto3.client")
    def test_model_send_mail_binds_identity(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_boto3_client.return_value = MagicMock()
        identity = SESIdentity(Identity="sender@example.com", IdentityType="EmailAddress")
        identity.set_session(None)
        destination = SESDestination(ToAddresses=["to@example.com"])
        message = SESMessage(
            Subject=SESContent(Data="hello"),
            Body=SESBody(Text=SESContent(Data="plain")),
        )

        with patch.object(SESIdentityManager, "send_mail", return_value="msg-456") as mock_send:
            message_id = identity.send_mail(
                destination,
                message,
                ConfigurationSetName="transactional",
            )

        mock_send.assert_called_once_with(
            "sender@example.com",
            destination,
            message,
            ReplyToAddresses=None,
            ReturnPath=None,
            SourceArn=None,
            ReturnPathArn=None,
            Tags=None,
            ConfigurationSetName="transactional",
        )
        assert message_id == "msg-456"

    @patch("boto3.client")
    def test_model_send_raw_mail_binds_identity(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_boto3_client.return_value = MagicMock()
        identity = SESIdentity(Identity="sender@example.com", IdentityType="EmailAddress")
        identity.set_session(None)
        raw_message = SESRawMessage(Data=b"raw-content")

        with patch.object(
            SESIdentityManager,
            "send_raw_mail",
            return_value="raw-456",
        ) as mock_send:
            message_id = identity.send_raw_mail(
                raw_message,
                Destinations=["to@example.com"],
            )

        mock_send.assert_called_once_with(
            "sender@example.com",
            raw_message,
            Destinations=["to@example.com"],
            FromArn=None,
            SourceArn=None,
            ReturnPathArn=None,
            Tags=None,
            ConfigurationSetName=None,
        )
        assert message_id == "raw-456"


class TestReceiptFilterManager:
    @patch("boto3.client")
    def test_list_receipt_filters_returns_public_models(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.list_receipt_filters.return_value = {
            "Filters": [
                {
                    "Name": "corp-cidr",
                    "IpFilter": {"Policy": "Allow", "Cidr": "10.0.0.0/8"},
                }
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = SESReceiptFilterManager()
        filters = manager.list()

        mock_client.list_receipt_filters.assert_called_once_with()
        assert isinstance(filters, PrimaryBoto3ModelQuerySet)
        assert len(filters) == 1
        assert isinstance(filters[0], SESReceiptFilter)
        assert filters[0].FilterName == "corp-cidr"
        assert filters[0].IpFilter is not None


class TestReceiptRuleSetManager:
    @patch("boto3.client")
    def test_get_receipt_rule_set_merges_metadata_and_rules(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.describe_receipt_rule_set.return_value = _receipt_rule_set_payload(
            "inbound"
        )
        mock_boto3_client.return_value = mock_client

        manager = SESReceiptRuleSetManager()
        rule_set = manager.get("inbound")

        mock_client.describe_receipt_rule_set.assert_called_once_with(
            RuleSetName="inbound"
        )
        assert isinstance(rule_set, SESReceiptRuleSet)
        assert rule_set.ReceiptRuleSetName == "inbound"
        assert rule_set.Rules is not None
        assert rule_set.Rules[0].ReceiptRuleName == "store-mail"
