"""Use case for getting element attribute."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class GetElementAttributeUsecase:
    """Gets a specific attribute from an element."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str, attribute: str) -> Result:
        """Get element attribute value.

        Args:
            identifier: Element identifier, label, or text
            attribute: Accessibility attribute name

        Returns:
            Result with attribute value
        """
        return self._repository.get_element_attribute(identifier, attribute)
