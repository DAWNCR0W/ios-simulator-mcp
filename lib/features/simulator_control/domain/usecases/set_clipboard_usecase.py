"""Use case for setting simulator clipboard text."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class SetClipboardUsecase:
    """Sets clipboard text via simctl."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, text: str, device_id: Optional[str]) -> Result[None]:
        """Execute the use case."""
        return self._repository.set_clipboard(text, device_id)
