class TaigaError(Exception):
    """Base exception for Taiga integration."""


class TaigaAuthenticationError(TaigaError):
    """Raised when Taiga authentication fails."""


class TaigaAPIError(TaigaError):
    """Raised when a Taiga API request fails."""
