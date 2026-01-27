"""Use case for installing an app on the simulator."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class InstallAppUsecase:
    """Installs an app bundle using simctl."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, app_path: str, device_id: Optional[str]) -> Result[None]:
        """Execute the use case."""
        return self._repository.install_app(app_path, device_id)
