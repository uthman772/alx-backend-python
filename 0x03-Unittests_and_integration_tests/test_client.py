#!/usr/bin/env python3
"""Test module for client.GithubOrgClient"""

import unittest
from parameterized import parameterized
from unittest.mock import patch, PropertyMock
from client import GithubOrgClient


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
