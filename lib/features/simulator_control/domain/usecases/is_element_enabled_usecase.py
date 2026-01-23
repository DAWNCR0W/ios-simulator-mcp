"""Use case for checking element enabled state."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class IsElementEnabledUsecase:
    """Checks if an element is enabled."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str) -> Result[bool]:
        """Check if element is enabled.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result with True if enabled, False otherwise
        """
        return self._repository.is_element_enabled(identifier)
