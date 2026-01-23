"""Use case for resetting an app on the simulator."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class ResetAppUsecase:
    """Resets an app using simctl."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Execute the use case."""
        return self._repository.reset_app(bundle_id, device_id)
