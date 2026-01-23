"""Domain entity representing an accessibility UI element."""

from dataclasses import dataclass, field
from typing import List, Optional

from lib.features.simulator_control.domain.entities.ui_frame import UiFrame


@dataclass(frozen=True)
class UiElement:
    """Represents a UI element node in the accessibility tree."""

    element_id: int
    role: str
    title: Optional[str]
    label: Optional[str]
    identifier: Optional[str]
    value: Optional[str]
    frame: Optional[UiFrame]
    children: List["UiElement"] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.element_id,
            "role": self.role,
            "title": self.title,
            "label": self.label,
            "identifier": self.identifier,
            "value": self.value,
            "frame": self.frame.to_dict() if self.frame else None,
            "children": [child.to_dict() for child in self.children],
        }
