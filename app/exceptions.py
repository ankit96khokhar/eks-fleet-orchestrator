class FleetUpgradeException(Exception):
    """Base exception for fleet upgrade system."""
    pass


class ConfigurationError(FleetUpgradeException):
    """Raised when configuration is invalid."""
    pass


class ValidationError(FleetUpgradeException):
    """Raised when cluster validation fails."""
    pass


class UpgradeFailedError(FleetUpgradeException):
    """Raised when cluster upgrade fails."""
    pass


class StateLockError(FleetUpgradeException):
    """Raised when cluster is already locked."""
    pass
