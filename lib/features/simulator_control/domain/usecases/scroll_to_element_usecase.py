"""Use case for scrolling to an element."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class ScrollToElementUsecase:
    """Scrolls until an element becomes visible."""

    DEFAULT_MAX_SCROLLS = 10
    DEFAULT_DIRECTION = "down"

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def execute(
        self,
        identifier: str,
        max_scrolls: int = DEFAULT_MAX_SCROLLS,
        direction: str = DEFAULT_DIRECTION,
    ) -> Result[dict]:
        """Execute scroll to element operation.

        Args:
            identifier: Element identifier to scroll to
            max_scrolls: Maximum number of scroll attempts
            direction: Scroll direction ('up' or 'down')

        Returns:
            Result with element info if found
        """
        return self._repository.scroll_to_element(identifier, max_scrolls, direction)
