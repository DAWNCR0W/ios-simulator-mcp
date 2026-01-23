"""Use case for waiting for an element to disappear."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class WaitForElementGoneUsecase:
    """Waits for an element to disappear from screen."""

    DEFAULT_TIMEOUT = 10.0

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str, timeout: float = DEFAULT_TIMEOUT) -> Result[None]:
        """Execute the wait for element gone operation.

        Args:
            identifier: Element identifier, label, or text
            timeout: Maximum time to wait in seconds

        Returns:
            Result success if element gone, failure if timeout
        """
        return self._repository.wait_for_element_gone(identifier, timeout)
