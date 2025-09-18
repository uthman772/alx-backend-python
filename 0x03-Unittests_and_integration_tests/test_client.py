#!/usr/bin/env python3
"""Test module for client.GithubOrgClient"""

import unittest
from parameterized import parameterized, parameterized_class
from unittest.mock import patch, PropertyMock
from client import GithubOrgClient
from fixtures import TEST_PAYLOAD


class TestGithubOrgClient(unittest.TestCase):
    """Test class for GithubOrgClient"""

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """Test that GithubOrgClient.org returns the correct value"""
        # Set up the mock return value
        expected_result = {"login": org_name, "id": 12345}
        mock_get_json.return_value = expected_result

        # Create client instance
        client = GithubOrgClient(org_name)

        # Call the org property
        result = client.org

        # Verify get_json was called once with the correct URL
        mock_get_json.assert_called_once_with(
            f"https://api.github.com/orgs/{org_name}"
        )
        
        # Verify the result is correct
        self.assertEqual(result, expected_result)

    def test_public_repos_url(self):
        """Test that GithubOrgClient._public_repos_url returns expected URL"""
        # Test payload with repos_url
        test_payload = {
            "repos_url": "https://api.github.com/orgs/testorg/repos"
        }
        
        # Create client instance
        client = GithubOrgClient("testorg")
        
        # Patch the org property to return our test payload
        with patch('client.GithubOrgClient.org', 
                  new_callable=PropertyMock,
                  return_value=test_payload):
            # Call the _public_repos_url property
            result = client._public_repos_url
            
            # Verify the result is the expected repos_url from the payload
            self.assertEqual(result, test_payload["repos_url"])

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """Test that GithubOrgClient.public_repos returns expected repos"""
        # Test payload for get_json (list of repos)
        test_repos_payload = [
            {"name": "repo1", "license": {"key": "mit"}},
            {"name": "repo2", "license": {"key": "apache-2.0"}},
            {"name": "repo3", "license": None},
        ]
        mock_get_json.return_value = test_repos_payload

        # Test value for _public_repos_url
        test_repos_url = "https://api.github.com/orgs/testorg/repos"

        # Create client instance
        client = GithubOrgClient("testorg")

        # Patch _public_repos_url to return our test URL
        with patch('client.GithubOrgClient._public_repos_url',
                  new_callable=PropertyMock,
                  return_value=test_repos_url) as mock_public_repos_url:
            
            # Call public_repos method
            result = client.public_repos()

            # Verify _public_repos_url was accessed once
            mock_public_repos_url.assert_called_once()
            
            # Verify get_json was called once with the test_repos_url
            mock_get_json.assert_called_once_with(test_repos_url)
            
            # Verify the result is the list of repo names
            expected_repos = ["repo1", "repo2", "repo3"]
            self.assertEqual(result, expected_repos)

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo, license_key, expected):
        """Test that GithubOrgClient.has_license returns expected result"""
        # Create client instance (org name doesn't matter for this test)
        client = GithubOrgClient("testorg")
        
        # Call has_license method with the test parameters
        result = client.has_license(repo, license_key)
        
        # Verify the result matches expected value
        self.assertEqual(result, expected)


@parameterized_class([
    {
        "org_payload": TEST_PAYLOAD[0][0],
        "repos_payload": TEST_PAYLOAD[0][1],
        "expected_repos": TEST_PAYLOAD[0][2],
        "apache2_repos": TEST_PAYLOAD[0][3],
    }
])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration test class for GithubOrgClient"""

    @classmethod
    def setUpClass(cls):
        """Set up class method to mock requests.get"""
        # Define the side_effect function to return different payloads based on URL
        def get_payload(url):
            """Return appropriate payload based on URL"""
            if url.endswith("/orgs/testorg"):
                return cls.org_payload
            elif url.endswith("/repos"):
                return cls.repos_payload
            return {}
        
        # Start the patcher for requests.get
        cls.get_patcher = patch('client.requests.get')
        mock_get = cls.get_patcher.start()
        
        # Configure the mock to return a response with json method
        mock_get.return_value.json.side_effect = get_payload

    @classmethod
    def tearDownClass(cls):
        """Tear down class method to stop the patcher"""
        cls.get_patcher.stop()

    def test_public_repos(self):
        """Integration test for public_repos method"""
        # Create client instance
        client = GithubOrgClient("testorg")
        
        # Call public_repos method
        result = client.public_repos()
        
        # Verify the result matches expected repos
        self.assertEqual(result, self.expected_repos)

    def test_public_repos_with_license(self):
        """Integration test for public_repos method with license filter"""
        # Create client instance
        client = GithubOrgClient("testorg")
        
        # Call public_repos method with license filter
        result = client.public_repos(license="apache-2.0")
        
        # Verify the result matches expected Apache2 repos
        self.assertEqual(result, self.apache2_repos)
