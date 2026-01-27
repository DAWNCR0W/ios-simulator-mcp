"""Use case for stopping a simulator screen recording."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class StopRecordingUsecase:
    """Stops simulator screen recording."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, device_id: Optional[str]) -> Result[dict]:
        """Execute the use case."""
        return self._repository.stop_recording(device_id)
