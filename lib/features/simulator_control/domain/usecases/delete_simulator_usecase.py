"""Use case for deleting a simulator device."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class DeleteSimulatorUsecase:
    """Deletes a simulator device by UDID."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, device_id: str) -> Result[None]:
        """Execute the use case."""
        return self._repository.delete_simulator(device_id)
