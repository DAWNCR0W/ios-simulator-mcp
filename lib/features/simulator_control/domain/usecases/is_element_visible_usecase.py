"""Use case for checking element visibility."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class IsElementVisibleUsecase:
    """Checks if an element is visible on screen."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str) -> Result[bool]:
        """Check if element is visible.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result with True if visible, False otherwise
        """
        return self._repository.is_element_visible(identifier)
