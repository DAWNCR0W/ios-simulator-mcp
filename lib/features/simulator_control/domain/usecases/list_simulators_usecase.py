"""Use case for listing simulator devices."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class ListSimulatorsUsecase:
    """Lists available simulator devices."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self) -> Result[list[dict]]:
        """Execute the use case."""
        return self._repository.list_simulators()
