"""Use case for erasing simulator data."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class EraseSimulatorUsecase:
    """Erases simulator data for a device or all devices."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, device_id: Optional[str], all_devices: bool) -> Result[dict]:
        """Execute the use case."""
        return self._repository.erase_simulator(device_id, all_devices)
