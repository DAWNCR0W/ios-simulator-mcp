"""Use case for managing simulator privacy permissions."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class SetPrivacyUsecase:
    """Updates simulator privacy permissions."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(
        self,
        action: str,
        service: str,
        bundle_id: Optional[str],
        device_id: Optional[str],
    ) -> Result[None]:
        """Execute the use case."""
        return self._repository.set_privacy(action, service, bundle_id, device_id)
