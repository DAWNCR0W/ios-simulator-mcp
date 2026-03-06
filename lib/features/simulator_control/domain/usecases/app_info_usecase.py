"""Use case for reading simulator app metadata."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class AppInfoUsecase:
    """Reads metadata for an installed simulator app."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, bundle_id: str, device_id: Optional[str]) -> Result[dict]:
        """Execute the use case."""
        return self._repository.app_info(bundle_id, device_id)
