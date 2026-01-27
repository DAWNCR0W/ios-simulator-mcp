"""Use case for resolving app container paths."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class GetAppContainerUsecase:
    """Resolves simulator app container paths."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(
        self, bundle_id: str, device_id: Optional[str], container_type: Optional[str]
    ) -> Result[dict]:
        """Execute the use case."""
        return self._repository.get_app_container(bundle_id, device_id, container_type)
