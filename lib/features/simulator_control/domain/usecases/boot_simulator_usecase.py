"""Use case for booting a simulator device."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class BootSimulatorUsecase:
    """Boots a simulator device using simctl."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, device_id: Optional[str]) -> Result[dict]:
        """Execute the use case."""
        return self._repository.boot_simulator(device_id)
