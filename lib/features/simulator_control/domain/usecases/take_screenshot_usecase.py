"""Use case for taking a simulator screenshot."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class TakeScreenshotUsecase:
    """Captures a simulator screenshot using simctl."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(
        self, device_id: Optional[str], output_path: Optional[str]
    ) -> Result[dict]:
        """Execute the use case."""
        return self._repository.take_screenshot(device_id, output_path)
