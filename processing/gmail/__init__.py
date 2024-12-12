"""Gmail integration module for newsletter processing."""

from .client import GmailClient
from .exceptions import GmailError, AuthenticationError, FetchError

__all__ = ['GmailClient', 'GmailError', 'AuthenticationError', 'FetchError']
