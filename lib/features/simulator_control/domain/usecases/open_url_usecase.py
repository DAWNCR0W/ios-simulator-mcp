"""Use case for opening a URL in the simulator."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class OpenUrlUsecase:
    """Opens a URL using simctl."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, url: str, device_id: Optional[str]) -> Result[None]:
        """Execute the use case."""
        return self._repository.open_url(url, device_id)
