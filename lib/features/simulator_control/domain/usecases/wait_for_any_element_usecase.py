"""Use case for waiting for any matching element."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class WaitForAnyElementUsecase:
    """Waits for any identifier in a set to appear on screen."""

    DEFAULT_TIMEOUT = 10.0

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifiers: list[str], timeout: float = DEFAULT_TIMEOUT) -> Result[dict]:
        """Execute the wait for any element operation.

        Args:
            identifiers: Candidate identifiers, labels, or text values to find
            timeout: Maximum time to wait in seconds

        Returns:
            Result with the matched identifier and element info if found
        """
        return self._repository.wait_for_any_element(identifiers, timeout)
