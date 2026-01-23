"""Use case for targeting a simulator window by title substring."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class SetTargetWindowUsecase:
    """Sets the simulator window title substring for UI operations."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, title_substring: Optional[str]) -> Result[dict]:
        """Store the title substring used to select a simulator window."""
        return self._repository.set_target_window_title(title_substring)
