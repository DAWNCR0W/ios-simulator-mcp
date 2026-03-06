"""Use case for getting supported element actions."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class GetElementActionsUsecase:
    """Gets supported accessibility actions from an element."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self, identifier: str) -> Result[list[str]]:
        """Get supported actions from a matching element.

        Args:
            identifier: Element identifier, label, title, or value text

        Returns:
            Result with supported action names
        """
        return self._repository.get_element_actions(identifier)
