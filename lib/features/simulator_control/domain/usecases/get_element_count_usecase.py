"""Use case for counting matching elements."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class GetElementCountUsecase:
    """Counts elements matching an identifier."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str) -> Result[int]:
        """Count matching elements.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result with count of matching elements
        """
        return self._repository.get_element_count(identifier)
