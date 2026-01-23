"""Data model representing a UI frame."""

from dataclasses import dataclass

from lib.features.simulator_control.domain.entities.ui_frame import UiFrame


@dataclass(frozen=True)
class UiFrameModel:
    """DTO for UI frame coming from Accessibility API."""

    x: float
    y: float
    width: float
    height: float

    def to_entity(self) -> UiFrame:
        """Convert to domain entity."""
        return UiFrame(x=self.x, y=self.y, width=self.width, height=self.height)
