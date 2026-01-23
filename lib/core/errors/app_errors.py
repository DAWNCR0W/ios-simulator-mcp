"""Custom exceptions used across the project."""


class SimulatorControlError(Exception):
    """Base exception for simulator control failures."""


class AccessibilityPermissionError(SimulatorControlError):
    """Raised when Accessibility permission is missing."""


class SimulatorNotRunningError(SimulatorControlError):
    """Raised when the iOS Simulator app is not running."""


class ElementNotFoundError(SimulatorControlError):
    """Raised when a requested UI element cannot be found."""


class SimctlError(SimulatorControlError):
    """Raised when a simctl command fails."""
