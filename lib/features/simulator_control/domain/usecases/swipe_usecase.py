"""Use case for performing swipe gestures."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class SwipeUsecase:
    """Performs swipe gestures."""

    DEFAULT_DISTANCE = 300.0
    DEFAULT_DURATION = 0.3

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(
        self,
        direction: str,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None,
        distance: float = DEFAULT_DISTANCE,
        duration: float = DEFAULT_DURATION,
    ) -> Result[None]:
        """Execute swipe gesture.

        Args:
            direction: 'up', 'down', 'left', or 'right'
            start_x: Starting X coordinate (defaults to center)
            start_y: Starting Y coordinate (defaults to center)
            distance: Swipe distance in pixels
            duration: Swipe duration in seconds

        Returns:
            Result indicating success or failure
        """
        return self._repository.swipe(direction, start_x, start_y, distance, duration)
