"""Use case for creating a simulator device."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class CreateSimulatorUsecase:
    """Creates a new simulator device."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, name: str, device_type_id: str, runtime_id: str) -> Result[dict]:
        """Execute the use case."""
        return self._repository.create_simulator(name, device_type_id, runtime_id)
