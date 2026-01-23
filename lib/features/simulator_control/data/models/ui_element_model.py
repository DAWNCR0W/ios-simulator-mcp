"""Data model representing a UI element."""

from dataclasses import dataclass, field
from typing import List, Optional

from lib.features.simulator_control.data.models.ui_frame_model import UiFrameModel
from lib.features.simulator_control.domain.entities.ui_element import UiElement


@dataclass(frozen=True)
class UiElementModel:
    """DTO for UI elements from Accessibility API."""

    element_id: int
    role: str
    title: Optional[str]
    label: Optional[str]
    identifier: Optional[str]
    value: Optional[str]
    frame: Optional[UiFrameModel]
    children: List["UiElementModel"] = field(default_factory=list)

    def to_entity(self) -> UiElement:
        """Convert to domain entity."""
        return UiElement(
            element_id=self.element_id,
            role=self.role,
            title=self.title,
            label=self.label,
            identifier=self.identifier,
            value=self.value,
            frame=self.frame.to_entity() if self.frame else None,
            children=[child.to_entity() for child in self.children],
        )
