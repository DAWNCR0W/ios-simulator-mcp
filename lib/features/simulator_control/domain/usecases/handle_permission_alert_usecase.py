"""Use case for handling system permission alerts."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class HandlePermissionAlertUsecase:
    """Handles permission alerts by tapping allow/deny buttons."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, action: str) -> Result[None]:
        """Execute the use case."""
        return self._repository.handle_permission_alert(action)
