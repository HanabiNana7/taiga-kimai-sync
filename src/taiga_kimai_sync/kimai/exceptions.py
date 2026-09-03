class KimaiError(Exception):
    """Base exception for Kimai integration."""


class KimaiAuthenticationError(KimaiError):
    """Raised when Kimai authentication fails."""


class KimaiAPIError(KimaiError):
    """Raised when a Kimai API request fails."""
