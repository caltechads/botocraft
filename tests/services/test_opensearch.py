from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.opensearch import OpenSearchDomain, OpenSearchDomainManager


def _minimal_domain_payload(name: str) -> dict[str, object]:
    """Return a minimal OpenSearch domain payload."""
    return {
        "DomainId": "domain-1",
        "DomainName": name,
        "ARN": f"arn:aws:es:us-west-2:123456789012:domain/{name}",
        "ClusterConfig": {"InstanceType": "t3.small.search"},
    }


class TestOpenSearchDomainManager:
    @patch("boto3.client")
    def test_list_domains_hydrates_domain_names(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.list_domain_names.return_value = {
            "DomainNames": [{"DomainName": "search-main"}],
        }
        mock_client.describe_domains.return_value = {
            "DomainStatusList": [_minimal_domain_payload("search-main")],
        }
        mock_client.list_tags.return_value = {
            "TagList": [{"Key": "Environment", "Value": "test"}],
        }
        mock_boto3_client.return_value = mock_client

        manager = OpenSearchDomainManager()
        domains = manager.list()

        mock_client.list_domain_names.assert_called_once_with()
        mock_client.describe_domains.assert_called_once_with(
            DomainNames=["search-main"],
        )
        mock_client.list_tags.assert_called_once_with(
            ARN="arn:aws:es:us-west-2:123456789012:domain/search-main",
        )
        assert isinstance(domains, PrimaryBoto3ModelQuerySet)
        assert len(domains) == 1
        assert isinstance(domains[0], OpenSearchDomain)
        assert domains[0].DomainName == "search-main"
        assert domains[0].Tags[0].Key == "Environment"
