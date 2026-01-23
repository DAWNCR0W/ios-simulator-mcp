"""Use case for getting element text content."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class GetElementTextUsecase:
    """Gets the text content of an element."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str) -> Result[str]:
        """Get element text content.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result with element's text content
        """
        return self._repository.get_element_text(identifier)
