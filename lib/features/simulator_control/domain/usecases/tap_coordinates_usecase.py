"""Use case for tapping a UI element by coordinates."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class TapCoordinatesUsecase:
    """Taps the simulator by absolute screen coordinates."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, x: float, y: float) -> Result[None]:
        """Tap the simulator at the provided coordinates."""
        return self._repository.tap_coordinates(x, y)
