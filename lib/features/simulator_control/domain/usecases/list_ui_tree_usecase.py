"""Use case for listing the UI tree."""

from lib.features.simulator_control.domain.entities.ui_element import UiElement
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class ListUiTreeUsecase:
    """Fetches the current UI tree from the simulator."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(self) -> UiElement:
        """Execute the use case."""
        return self._repository.get_ui_tree()
