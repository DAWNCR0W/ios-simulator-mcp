"""Use case for long press gestures."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class LongPressUsecase:
    """Performs long press on an element."""

    DEFAULT_DURATION = 1.0

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str, duration: float = DEFAULT_DURATION) -> Result[None]:
        """Execute long press on element.

        Args:
            identifier: Element identifier, label, or text
            duration: Press duration in seconds

        Returns:
            Result indicating success or failure
        """
        return self._repository.long_press(identifier, duration)
