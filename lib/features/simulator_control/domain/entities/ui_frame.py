"""Domain entity representing a UI element frame."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UiFrame:
    """Represents a rectangle in screen coordinates."""

    x: float
    y: float
    width: float
    height: float

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
