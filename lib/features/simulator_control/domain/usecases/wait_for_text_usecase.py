"""Use case for waiting for text to appear."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class WaitForTextUsecase:
    """Waits for specific text to appear on screen."""

    DEFAULT_TIMEOUT = 10.0

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, text: str, timeout: float = DEFAULT_TIMEOUT) -> Result[dict]:
        """Execute the wait for text operation.

        Args:
            text: Text to search for
            timeout: Maximum time to wait in seconds

        Returns:
            Result with element info containing the text if found
        """
        return self._repository.wait_for_text(text, timeout)
