"""Tests for Gmail client implementation."""

import os
import json
import pytest
from unittest.mock import Mock, patch, mock_open
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from processing.gmail.client import GmailClient
from processing.gmail.exceptions import AuthenticationError, FetchError

@pytest.fixture
def mock_credentials():
    """Fixture for mock credentials data."""
    return {
        "token": "mock_token",
        "refresh_token": "mock_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "mock_client_id",
        "client_secret": "mock_client_secret",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
    }

@pytest.fixture
def mock_message():
    """Fixture for mock Gmail message data."""
    return {
        'id': 'msg123',
        'threadId': 'thread123',
        'labelIds': ['GenAI News', 'INBOX'],
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Newsletter'},
                {'name': 'Date', 'value': '2024-01-15T10:00:00Z'}
            ],
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {
                        'data': 'VGVzdCBjb250ZW50'  # Base64 encoded "Test content"
                    }
                }
            ]
        }
    }

@pytest.fixture
def mock_labels():
    """Fixture for mock Gmail labels data."""
    return {
        'labels': [
            {'id': 'label123', 'name': 'GenAI News'},
            {'id': 'label456', 'name': 'INBOX'}
        ]
    }

class TestGmailClient:
    """Test cases for GmailClient class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.credentials_path = 'credentials.json'
        self.token_path = 'token.json'

    @patch('processing.gmail.client.Credentials')
    @patch('processing.gmail.client.build')
    def test_successful_authentication_with_existing_token(self, mock_build, mock_creds):
        """Test successful authentication with existing valid token."""
        # Setup
        mock_cred_instance = Mock(spec=Credentials)
        mock_cred_instance.valid = True
        mock_creds.from_authorized_user_file.return_value = mock_cred_instance
        
        # Create client
        with patch('os.path.exists', return_value=True):
            client = GmailClient(self.credentials_path, self.token_path)
        
        # Verify
        assert client.service is not None
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_cred_instance)

    @patch('processing.gmail.client.InstalledAppFlow')
    @patch('processing.gmail.client.build')
    def test_authentication_with_new_flow(self, mock_build, mock_flow):
        """Test authentication with new OAuth flow."""
        # Setup
        mock_creds = Mock(spec=Credentials)
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_creds
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance
        
        # Create client
        with patch('os.path.exists', return_value=False):
            with patch('builtins.open', mock_open()):
                client = GmailClient(self.credentials_path, self.token_path)
        
        # Verify
        mock_flow.from_client_secrets_file.assert_called_once_with(
            self.credentials_path, GmailClient.SCOPES)
        assert client.service is not None

    @patch('processing.gmail.client.build')
    def test_authentication_failure(self, mock_build):
        """Test authentication failure handling."""
        # Setup
        mock_build.side_effect = Exception("Auth failed")
        
        # Verify
        with pytest.raises(AuthenticationError):
            with patch('os.path.exists', return_value=False):
                GmailClient(self.credentials_path, self.token_path)

    @patch('processing.gmail.client.build')
    def test_successful_newsletter_fetch(self, mock_build, mock_message, mock_labels):
        """Test successful newsletter fetching."""
        # Setup
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Mock Gmail API responses
        mock_service.users().labels().list().execute.return_value = mock_labels
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg123'}]
        }
        mock_service.users().messages().get().execute.return_value = mock_message
        
        # Create client and fetch newsletters
        with patch('os.path.exists', return_value=True):
            client = GmailClient(self.credentials_path, self.token_path)
            newsletters = client.get_newsletters(max_results=1)
        
        # Verify
        assert len(newsletters) == 1
        assert newsletters[0]['email_id'] == 'msg123'
        assert newsletters[0]['subject'] == 'Test Newsletter'
        assert newsletters[0]['content'] == 'Test content'

    @patch('processing.gmail.client.build')
    def test_fetch_with_missing_label(self, mock_build, mock_labels):
        """Test newsletter fetching when label doesn't exist."""
        # Setup
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Mock Gmail API response without newsletter label
        mock_labels_without_newsletter = {'labels': [{'id': 'label456', 'name': 'INBOX'}]}
        mock_service.users().labels().list().execute.return_value = mock_labels_without_newsletter
        
        # Create client and fetch newsletters
        with patch('os.path.exists', return_value=True):
            client = GmailClient(self.credentials_path, self.token_path)
            newsletters = client.get_newsletters()
        
        # Verify
        assert len(newsletters) == 0

    @patch('processing.gmail.client.build')
    def test_fetch_error_handling(self, mock_build):
        """Test error handling during newsletter fetching."""
        # Setup
        mock_service = Mock()
        mock_build.return_value = mock_service
        mock_service.users().labels().list().execute.side_effect = HttpError(
            resp=Mock(status=500), content=b'Server error'
        )
        
        # Create client and attempt to fetch newsletters
        with patch('os.path.exists', return_value=True):
            client = GmailClient(self.credentials_path, self.token_path)
            with pytest.raises(FetchError):
                client.get_newsletters()

    @patch('processing.gmail.client.build')
    def test_message_parsing_error_handling(self, mock_build, mock_labels):
        """Test error handling during message parsing."""
        # Setup
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Mock Gmail API responses
        mock_service.users().labels().list().execute.return_value = mock_labels
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg123'}]
        }
        # Return invalid message data to trigger parsing error
        mock_service.users().messages().get().execute.return_value = {'id': 'msg123'}
        
        # Create client and fetch newsletters
        with patch('os.path.exists', return_value=True):
            client = GmailClient(self.credentials_path, self.token_path)
            newsletters = client.get_newsletters()
        
        # Verify that parsing error is handled gracefully
        assert len(newsletters) == 0
