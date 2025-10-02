class BotocraftError(Exception):
    """Exception raised when a botocraft error occurs."""


class NotUpdatableError(BotocraftError):
    """Exception raised when a resource is not updatable."""


class CannotDeleteError(BotocraftError):
    """Exception raised when a resource cannot be deleted."""


class CannotCreateError(BotocraftError):
    """Exception raised when a resource cannot be created."""

