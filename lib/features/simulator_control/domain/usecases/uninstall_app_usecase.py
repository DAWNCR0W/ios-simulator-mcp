"""Use case for uninstalling an app from the simulator."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class UninstallAppUsecase:
    """Uninstalls an app bundle using simctl."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Execute the use case."""
        return self._repository.uninstall_app(bundle_id, device_id)
