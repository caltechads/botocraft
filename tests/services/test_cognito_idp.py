from unittest.mock import MagicMock, patch

from botocraft.services.cognito_idp import CognitoUserManager


class TestCognitoUserManagerPasswords:
    @patch("boto3.client")
    def test_set_password_calls_admin_set_user_password(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        manager = CognitoUserManager()

        password = "new-secret"  # noqa: S105
        manager.set_password(
            UserPoolId="us-west-2_pool",
            Username="alice",
            Password=password,
            Permanent=True,
        )

        mock_client.admin_set_user_password.assert_called_once_with(
            UserPoolId="us-west-2_pool",
            Username="alice",
            Password=password,
            Permanent=True,
        )

    @patch("boto3.client")
    def test_reset_password_calls_admin_reset_user_password(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        manager = CognitoUserManager()

        manager.reset_password(
            UserPoolId="us-west-2_pool",
            Username="alice",
            ClientMetadata={"reason": "lost"},
        )

        mock_client.admin_reset_user_password.assert_called_once_with(
            UserPoolId="us-west-2_pool",
            Username="alice",
            ClientMetadata={"reason": "lost"},
        )
