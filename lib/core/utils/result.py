"""Result wrapper used across layers."""

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    """Represents a success/failure outcome with optional payload."""

    is_success: bool
    message: str
    data: Optional[T] = None

    @staticmethod
    def success(data: Optional[T] = None, message: str = "OK") -> "Result[T]":
        """Create a successful result."""
        return Result(is_success=True, message=message, data=data)

    @staticmethod
    def failure(message: str) -> "Result[T]":
        """Create a failed result."""
        return Result(is_success=False, message=message, data=None)

    def to_dict(self) -> dict:
        """Convert to a JSON-serializable dict."""
        payload = self.data
        if hasattr(payload, "to_dict"):
            payload = payload.to_dict()
        return {
            "success": self.is_success,
            "message": self.message,
            "data": payload,
        }
