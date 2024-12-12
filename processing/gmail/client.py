"""Gmail client implementation for newsletter processing."""

import os
import base64
import logging
from typing import List, Dict, Optional
from datetime import datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .exceptions import AuthenticationError, FetchError

# Configure logging
logger = logging.getLogger(__name__)

class GmailClient:
    """Client for interacting with Gmail API to fetch newsletters."""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    NEWSLETTER_LABEL = 'GenAI News'

    def __init__(self, credentials_path: str, token_path: str):
        """
        Initialize the Gmail client.

        Args:
            credentials_path: Path to the credentials.json file
            token_path: Path to store/retrieve the token.json file
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """
        Authenticate with Gmail API using OAuth 2.0.

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            creds = None
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)

                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())

            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Successfully authenticated with Gmail API")

        except Exception as e:
            logger.error(f"Failed to authenticate with Gmail API: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def get_newsletters(self, max_results: int = 10) -> List[Dict]:
        """
        Fetch newsletters with the specified label.

        Args:
            max_results: Maximum number of newsletters to fetch

        Returns:
            List of dictionaries containing newsletter data

        Raises:
            FetchError: If fetching newsletters fails
        """
        try:
            # Get label ID for newsletter label
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            label_id = next(
                (label['id'] for label in labels if label['name'] == self.NEWSLETTER_LABEL),
                None
            )

            if not label_id:
                logger.warning(f"Label '{self.NEWSLETTER_LABEL}' not found")
                return []

            # Fetch emails with the newsletter label
            results = self.service.users().messages().list(
                userId='me',
                labelIds=[label_id],
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            newsletters = []

            for message in messages:
                msg_data = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                newsletter = self._parse_message(msg_data)
                if newsletter:
                    newsletters.append(newsletter)

            logger.info(f"Successfully fetched {len(newsletters)} newsletters")
            return newsletters

        except HttpError as e:
            logger.error(f"Failed to fetch newsletters: {str(e)}")
            raise FetchError(f"Failed to fetch newsletters: {str(e)}")

    def _parse_message(self, message: Dict) -> Optional[Dict]:
        """
        Parse Gmail message into newsletter data.

        Args:
            message: Raw message data from Gmail API

        Returns:
            Dictionary containing parsed newsletter data or None if parsing fails
        """
        try:
            headers = message['payload']['headers']
            subject = next(
                (header['value'] for header in headers if header['name'].lower() == 'subject'),
                'No Subject'
            )
            date = next(
                (header['value'] for header in headers if header['name'].lower() == 'date'),
                None
            )

            # Get message body
            if 'parts' in message['payload']:
                parts = message['payload']['parts']
                content = ''
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            content += base64.urlsafe_b64decode(data).decode()
            else:
                data = message['payload']['body'].get('data', '')
                content = base64.urlsafe_b64decode(data).decode() if data else ''

            return {
                'email_id': message['id'],
                'subject': subject,
                'received_date': date,
                'content': content,
                'metadata': {
                    'thread_id': message['threadId'],
                    'label_ids': message.get('labelIds', [])
                }
            }

        except Exception as e:
            logger.error(f"Failed to parse message {message.get('id')}: {str(e)}")
            return None
