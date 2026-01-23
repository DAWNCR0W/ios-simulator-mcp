"""Use case for waiting for an element to appear."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class WaitForElementUsecase:
    """Waits for an element to appear on screen."""

    DEFAULT_TIMEOUT = 10.0

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str, timeout: float = DEFAULT_TIMEOUT) -> Result[dict]:
        """Execute the wait for element operation.

        Args:
            identifier: Element identifier, label, or text to find
            timeout: Maximum time to wait in seconds

        Returns:
            Result with element info if found, failure if timeout
        """
        return self._repository.wait_for_element(identifier, timeout)
