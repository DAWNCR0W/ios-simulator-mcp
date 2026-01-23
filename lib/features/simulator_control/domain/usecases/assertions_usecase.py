"""Use case for UI assertions."""

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class AssertionsUsecase:
    """Provides assertion methods for UI testing."""

    def __init__(self, repository: SimulatorRepository) -> None:
        self._repository = repository

    def assert_element_exists(self, identifier: str) -> Result[None]:
        """Assert that an element exists.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result success if exists, failure if not
        """
        return self._repository.assert_element_exists(identifier)

    def assert_element_not_exists(self, identifier: str) -> Result[None]:
        """Assert that an element does not exist.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result success if not exists, failure if exists
        """
        return self._repository.assert_element_not_exists(identifier)

    def assert_element_visible(self, identifier: str) -> Result[None]:
        """Assert that an element is visible.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result success if visible, failure if not
        """
        return self._repository.assert_element_visible(identifier)

    def assert_element_enabled(self, identifier: str) -> Result[None]:
        """Assert that an element is enabled.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result success if enabled, failure if not
        """
        return self._repository.assert_element_enabled(identifier)

    def assert_text_equals(self, identifier: str, expected: str) -> Result[None]:
        """Assert that element text equals expected value.

        Args:
            identifier: Element identifier, label, or text
            expected: Expected text value

        Returns:
            Result success if text matches, failure if not
        """
        return self._repository.assert_text_equals(identifier, expected)

    def assert_text_contains(self, identifier: str, substring: str) -> Result[None]:
        """Assert that element text contains substring.

        Args:
            identifier: Element identifier, label, or text
            substring: Expected substring

        Returns:
            Result success if text contains substring, failure if not
        """
        return self._repository.assert_text_contains(identifier, substring)

    def assert_element_count(self, identifier: str, expected_count: int) -> Result[None]:
        """Assert the count of matching elements.

        Args:
            identifier: Element identifier, label, or text
            expected_count: Expected number of matching elements

        Returns:
            Result success if count matches, failure if not
        """
        return self._repository.assert_element_count(identifier, expected_count)
