"""Use case for listing installed apps on the simulator."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class ListInstalledAppsUsecase:
    """Lists installed apps on the simulator."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, device_id: Optional[str]) -> Result[list[dict]]:
        """Execute the use case."""
        return self._repository.list_installed_apps(device_id)
