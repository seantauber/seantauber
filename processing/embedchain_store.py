"""Embedchain integration for vector storage."""

import logging
from typing import Dict, Optional, List
from embedchain import App
from google.oauth2.credentials import Credentials
import googleapiclient
from googleapiclient.discovery import build
import base64

logger = logging.getLogger(__name__)

class EmbedchainStore:
    """Vector storage implementation using Embedchain."""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    NEWSLETTER_LABEL = 'GenAI News'

    def __init__(self, credentials_path: str):
        """
        Initialize Embedchain store.

        Args:
            credentials_path: Path to Gmail API credentials
        """
        # Initialize Gmail API
        self.credentials_path = credentials_path
        self.creds = Credentials.from_authorized_user_file(credentials_path, self.SCOPES)
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        
        # Initialize Embedchain apps for different collections
        self.newsletter_store = App(
            config={
                "collection_name": "newsletters",
                "chunking": {
                    "chunk_size": 500,
                    "chunk_overlap": 50
                }
            }
        )
        
        self.repository_store = App(
            config={
                "collection_name": "repositories",
                "chunking": {
                    "chunk_size": 500,
                    "chunk_overlap": 50
                }
            }
        )

    def _get_label_id(self) -> Optional[str]:
        """Get Gmail label ID for newsletter label."""
        try:
            results = self.gmail_service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            label_id = next(
                (label['id'] for label in labels if label['name'] == self.NEWSLETTER_LABEL),
                None
            )
            return label_id
        except Exception as e:
            logger.error(f"Failed to get label ID: {str(e)}")
            raise

    async def load_and_store_newsletters(self, max_results: int = 10) -> List[str]:
        """
        Load newsletters from Gmail and store in vector storage.

        Args:
            max_results: Maximum number of newsletters to fetch

        Returns:
            List of vector IDs for stored newsletters

        Raises:
            Exception: If loading or storing fails
        """
        try:
            label_id = self._get_label_id()
            if not label_id:
                logger.warning(f"Label '{self.NEWSLETTER_LABEL}' not found")
                return []

            # Fetch emails with newsletter label
            results = self.gmail_service.users().messages().list(
                userId='me',
                labelIds=[label_id],
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            vector_ids = []

            for message in messages:
                msg = self.gmail_service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                # Extract headers
                headers = msg['payload']['headers']
                subject = next(
                    (header['value'] for header in headers if header['name'].lower() == 'subject'),
                    'No Subject'
                )
                sender = next(
                    (header['value'] for header in headers if header['name'].lower() == 'from'),
                    'Unknown Sender'
                )
                date = next(
                    (header['value'] for header in headers if header['name'].lower() == 'date'),
                    None
                )

                # Extract body
                if 'parts' in msg['payload']:
                    parts = msg['payload']['parts']
                    data = parts[0]['body'].get('data', '')
                else:
                    data = msg['payload']['body'].get('data', '')

                body = base64.urlsafe_b64decode(data).decode('utf-8') if data else ''

                # Store in vector storage
                vector_id = self.newsletter_store.add(
                    content=f"Email from {sender}: {subject}\n\n{body}",
                    metadata={
                        'email_id': message['id'],
                        'subject': subject,
                        'sender': sender,
                        'received_date': date
                    }
                )
                vector_ids.append(vector_id)
                logger.info(f"Stored newsletter {message['id']} in vector storage")

            return vector_ids

        except Exception as e:
            logger.error(f"Failed to load and store newsletters: {str(e)}")
            raise

    async def store_repository(self, repository: Dict) -> str:
        """
        Store repository data in vector storage.

        Args:
            repository: Repository data including description and metadata

        Returns:
            Vector storage ID

        Raises:
            Exception: If storing fails
        """
        try:
            vector_id = self.repository_store.add(
                content=repository['description'],
                metadata={
                    'github_url': repository['github_url'],
                    'first_seen_date': repository['first_seen_date']
                }
            )
            logger.info(f"Stored repository {repository['github_url']} in vector storage")
            return vector_id
        except Exception as e:
            logger.error(f"Failed to store repository in vector storage: {str(e)}")
            raise

    async def query_newsletters(
        self,
        query: str,
        limit: int = 5
    ) -> list:
        """
        Search through stored newsletters.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of relevant newsletter content
        """
        try:
            results = self.newsletter_store.query(
                query,
                top_k=limit
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query newsletters: {str(e)}")
            raise

    async def query_repositories(
        self,
        query: str,
        limit: int = 5
    ) -> list:
        """
        Search through stored repositories.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of relevant repository content
        """
        try:
            results = self.repository_store.query(
                query,
                top_k=limit
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query repositories: {str(e)}")
            raise
