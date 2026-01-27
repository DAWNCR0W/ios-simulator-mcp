"""Use case for adding media to the simulator."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class AddMediaUsecase:
    """Adds media files to the simulator photo library."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, media_paths: list[str], device_id: Optional[str]) -> Result[dict]:
        """Execute the use case."""
        return self._repository.add_media(media_paths, device_id)
