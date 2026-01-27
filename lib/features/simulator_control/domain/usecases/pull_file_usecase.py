"""Use case for pulling files from the simulator."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class PullFileUsecase:
    """Pulls files from the simulator."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(
        self, source_path: str, destination_path: str, device_id: Optional[str]
    ) -> Result[None]:
        """Execute the use case."""
        return self._repository.pull_file(source_path, destination_path, device_id)
