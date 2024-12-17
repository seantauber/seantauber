"""Embedchain integration for vector storage."""

import os
import json
import logging
import socket
from typing import Dict, Optional, List, Tuple, Any
from embedchain import App
from embedchain.config import AppConfig
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient
from googleapiclient.discovery import build
import base64

logger = logging.getLogger(__name__)

class EmbedchainStore:
    """Vector storage implementation using Embedchain."""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    NEWSLETTER_LABEL = 'GenAI News'
    BASE_PORT = 8029  # Base port to start trying from
    MAX_PORT_ATTEMPTS = 10  # Maximum number of ports to try

    def __init__(self, token_path: str):
        """
        Initialize Embedchain store.

        Args:
            token_path: Path to Gmail API token
        """
        # Initialize Gmail API with proper credential handling
        self.token_path = token_path
        self.creds = self._get_credentials()
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        
        # Initialize Embedchain apps for different collections
        self.newsletter_store = App()
        self.repository_store = App()
        
        # Cache for repository data
        self._repository_cache: Dict[str, Dict[str, Any]] = {}

    def _find_available_port(self) -> Tuple[int, bool]:
        """Find an available port starting from BASE_PORT."""
        for port_offset in range(self.MAX_PORT_ATTEMPTS):
            port = self.BASE_PORT + port_offset
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('localhost', port))
                sock.close()
                is_base_port = port == self.BASE_PORT
                return port, is_base_port
            except OSError:
                continue
            finally:
                sock.close()
        raise OSError(f"Could not find an available port after {self.MAX_PORT_ATTEMPTS} attempts")

    def _validate_token_data(self, token_data: dict) -> bool:
        """Validate token data has all required fields."""
        required_fields = ['refresh_token', 'token', 'token_uri', 'client_id', 'client_secret']
        return all(field in token_data for field in required_fields)

    def _get_credentials(self) -> Credentials:
        """Get or refresh Google API credentials."""
        creds = None
        
        # Check if token file exists and contains valid data
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path) as f:
                    token_data = json.load(f)
                if not self._validate_token_data(token_data):
                    logger.warning("Token file exists but missing required fields")
                    os.remove(self.token_path)  # Remove invalid token file
                else:
                    creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                logger.warning(f"Error reading token file: {e}")
                os.remove(self.token_path)  # Remove invalid token file

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")
                    os.remove(self.token_path)  # Remove invalid token file
                    creds = None
            
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(
                    ".credentials/google-credentials.json", self.SCOPES)
                
                # Find an available port
                try:
                    port, is_base_port = self._find_available_port()
                    if not is_base_port:
                        logger.warning(
                            f"Base port {self.BASE_PORT} is in use, using alternative port {port}"
                        )
                    
                    # Use found port and request offline access for refresh token
                    # Note: Adding trailing slash to match the redirect URI exactly
                    redirect_uri = f"http://localhost:{port}/"
                    flow.redirect_uri = redirect_uri
                    
                    creds = flow.run_local_server(
                        port=port,
                        access_type='offline',  # Enable offline access
                        prompt='consent',  # Force consent screen to get refresh token
                        authorization_prompt_message=(
                            f"Please visit this URL to authorize this application "
                            f"(using port {port} for callback)"
                        )
                    )
                except OSError as e:
                    logger.error("Failed to start local server for OAuth flow")
                    raise RuntimeError(
                        f"OAuth flow failed: Could not start local server. "
                        f"Please ensure no other OAuth flows are running and try again. "
                        f"Error: {str(e)}"
                    )

            # Validate we got a refresh token
            if not creds.refresh_token:
                raise RuntimeError(
                    "Failed to obtain refresh token. Please ensure you're logged out of "
                    "all Google accounts and try again to see the consent screen."
                )

            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return creds

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

                # Store in vector storage using message ID as source
                vector_id = self.newsletter_store.add(
                    body,  # Store the actual content
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

    async def store_repository(self, repository: Dict[str, Any]) -> str:
        """
        Store repository data in vector storage.

        Args:
            repository: Repository data including metadata and summary

        Returns:
            Vector storage ID

        Raises:
            Exception: If storing fails
        """
        try:
            # Create searchable text representation
            search_text = (
                f"Repository: {repository['name']} ({repository['github_url']})\n"
                f"Description: {repository['description']}\n"
                f"Language: {repository['metadata']['language']}\n"
                f"Topics: {', '.join(repository['metadata']['topics'])}\n"
                f"Primary Purpose: {repository['summary']['primary_purpose']}\n"
                f"Technical Domain: {repository['summary']['technical_domain']}"
            )
            
            # Store with minimal metadata for search
            vector_id = self.repository_store.add(
                search_text,
                metadata={
                    'github_url': repository['github_url'],
                    'name': repository['name']
                }
            )
            
            # Cache complete repository data
            self._repository_cache[repository['github_url']] = repository
            
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
            # Get search results
            results = self.repository_store.query(
                query,
                top_k=limit
            )
            
            # Extract stored data from cache
            processed_results = []
            for result in results:
                try:
                    # Handle string response format
                    if isinstance(result, str):
                        # Try to extract github_url from the text
                        import re
                        url_match = re.search(r'https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+', result)
                        if url_match:
                            github_url = url_match.group(0)
                            if github_url in self._repository_cache:
                                processed_results.append(self._repository_cache[github_url])
                            else:
                                logger.warning(f"Repository not found in cache: {github_url}")
                        else:
                            logger.warning(f"Could not extract GitHub URL from result: {result}")
                    else:
                        processed_results.append(result)
                except Exception as e:
                    logger.warning(f"Error processing result: {str(e)}")
                    continue
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Failed to query repositories: {str(e)}")
            raise

    async def get_embedding(self, vector_id: str) -> Optional[List[float]]:
        """
        Get the embedding vector for a stored item.
        
        Args:
            vector_id: Vector storage ID
            
        Returns:
            Embedding vector if found, None otherwise
        """
        try:
            # Try both stores since we don't know which one contains the ID
            try:
                embedding = self.newsletter_store.get(vector_id)
                return embedding
            except:
                embedding = self.repository_store.get(vector_id)
                return embedding
        except Exception as e:
            logger.error(f"Failed to get embedding for vector ID {vector_id}: {str(e)}")
            return None
