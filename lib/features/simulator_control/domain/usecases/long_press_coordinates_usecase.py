"""Use case for long press at coordinates."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class LongPressCoordinatesUsecase:
    """Performs long press at specific coordinates."""

    DEFAULT_DURATION = 1.0

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(
        self, x: float, y: float, duration: float = DEFAULT_DURATION
    ) -> Result[None]:
        """Execute long press at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds

        Returns:
            Result indicating success or failure
        """
        return self._repository.long_press_coordinates(x, y, duration)
