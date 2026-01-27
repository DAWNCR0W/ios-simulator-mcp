"""Use case for reading simulator clipboard text."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class GetClipboardUsecase:
    """Fetches clipboard text via simctl."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, device_id: Optional[str]) -> Result[str]:
        """Execute the use case."""
        return self._repository.get_clipboard(device_id)
