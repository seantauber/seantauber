"""Custom exceptions for Gmail integration."""

class GmailError(Exception):
    """Base exception for Gmail-related errors."""
    pass

class AuthenticationError(GmailError):
    """Raised when Gmail authentication fails."""
    pass

class FetchError(GmailError):
    """Raised when fetching emails fails."""
    pass
