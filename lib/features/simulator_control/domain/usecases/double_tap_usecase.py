"""Use case for double-tap gestures."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class DoubleTapUsecase:
    """Performs a double tap on an element."""

    DEFAULT_INTERVAL = 0.1

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(
        self,
        identifier: str,
        interval: float = DEFAULT_INTERVAL,
    ) -> Result[None]:
        """Execute a double tap on an element.

        Args:
            identifier: Element identifier, label, or text.
            interval: Delay between taps in seconds.

        Returns:
            Result indicating success or failure.
        """
        return self._repository.double_tap(identifier, interval)
