"""Use case for tapping a UI element."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class TapElementUsecase:
    """Taps a UI element by identifier or label."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str) -> Result[None]:
        """Execute the use case."""
        return self._repository.tap_element(identifier)
