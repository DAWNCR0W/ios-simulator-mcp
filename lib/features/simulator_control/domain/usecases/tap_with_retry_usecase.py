"""Use case for tapping with retry."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class TapWithRetryUsecase:
    """Taps an element with automatic retry on failure."""

    DEFAULT_RETRIES = 3
    DEFAULT_INTERVAL = 0.5

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(
        self,
        identifier: str,
        retries: int = DEFAULT_RETRIES,
        interval: float = DEFAULT_INTERVAL,
    ) -> Result[None]:
        """Execute tap with retry.

        Args:
            identifier: Element identifier, label, or text
            retries: Maximum number of retry attempts
            interval: Delay between retries in seconds

        Returns:
            Result indicating success or failure
        """
        return self._repository.tap_element_with_retry(identifier, retries, interval)
