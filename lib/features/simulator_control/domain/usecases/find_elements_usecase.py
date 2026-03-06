"""Use case for finding matching elements."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class FindElementsUsecase:
    """Finds elements matching a query string."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, query: str, max_results: int = 10) -> Result[list[dict]]:
        """Find matching elements.

        Args:
            query: Identifier, label, title, or value text to match
            max_results: Maximum number of results to return

        Returns:
            Result with matching element metadata
        """
        return self._repository.find_elements(query, max_results)
