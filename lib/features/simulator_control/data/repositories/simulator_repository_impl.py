"""Repository implementation for simulator control."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.data.datasources.accessibility_datasource import (
    AccessibilityDatasource,
)
from lib.features.simulator_control.data.datasources.simctl_datasource import SimctlDatasource
from lib.features.simulator_control.domain.entities.ui_element import UiElement
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)


class SimulatorRepositoryImpl(SimulatorRepository):
    """Connects domain use cases with underlying datasources."""

    def __init__(
        self,
        accessibility_datasource: AccessibilityDatasource,
        simctl_datasource: SimctlDatasource,
    ) -> None:
        self._accessibility_datasource = accessibility_datasource
        self._simctl_datasource = simctl_datasource

    # =========================================================================
    # CORE OPERATIONS
    # =========================================================================

    def get_ui_tree(self) -> UiElement:
        ui_tree = self._accessibility_datasource.get_ui_tree()
        return ui_tree.to_entity()

    def tap_element(self, identifier: str) -> Result[None]:
        return self._accessibility_datasource.tap_element(identifier)

    def tap_coordinates(self, x: float, y: float) -> Result[None]:
        return self._accessibility_datasource.tap_coordinates(x, y)

    def input_text(self, identifier: str, text: str) -> Result[None]:
        return self._accessibility_datasource.input_text(identifier, text)

    def launch_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        return self._simctl_datasource.launch_app(bundle_id, device_id)

    def stop_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        return self._simctl_datasource.stop_app(bundle_id, device_id)

    def reset_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        return self._simctl_datasource.reset_app(bundle_id, device_id)

    def list_simulators(self) -> Result[list[dict]]:
        return self._simctl_datasource.list_simulators()

    def take_screenshot(
        self, device_id: Optional[str], output_path: Optional[str]
    ) -> Result[dict]:
        return self._simctl_datasource.take_screenshot(device_id, output_path)

    def handle_permission_alert(self, action: str) -> Result[None]:
        return self._accessibility_datasource.handle_permission_alert(action)

    def set_target_window_title(self, title_substring: Optional[str]) -> Result[dict]:
        return self._accessibility_datasource.set_target_window_title(title_substring)

    # =========================================================================
    # WAIT UTILITIES
    # =========================================================================

    def wait_for_element(self, identifier: str, timeout: float) -> Result[dict]:
        return self._accessibility_datasource.wait_for_element(identifier, timeout)

    def wait_for_element_gone(self, identifier: str, timeout: float) -> Result[None]:
        return self._accessibility_datasource.wait_for_element_gone(identifier, timeout)

    def wait_for_text(self, text: str, timeout: float) -> Result[dict]:
        return self._accessibility_datasource.wait_for_text(text, timeout)

    # =========================================================================
    # ELEMENT STATE CHECKS
    # =========================================================================

    def is_element_visible(self, identifier: str) -> Result[bool]:
        return self._accessibility_datasource.is_element_visible(identifier)

    def is_element_enabled(self, identifier: str) -> Result[bool]:
        return self._accessibility_datasource.is_element_enabled(identifier)

    def get_element_text(self, identifier: str) -> Result[str]:
        return self._accessibility_datasource.get_element_text(identifier)

    def get_element_attribute(self, identifier: str, attribute: str) -> Result:
        return self._accessibility_datasource.get_element_attribute(identifier, attribute)

    def get_element_count(self, identifier: str) -> Result[int]:
        return self._accessibility_datasource.get_element_count(identifier)

    # =========================================================================
    # GESTURE SUPPORT
    # =========================================================================

    def swipe(
        self,
        direction: str,
        start_x: Optional[float],
        start_y: Optional[float],
        distance: float,
        duration: float,
    ) -> Result[None]:
        return self._accessibility_datasource.swipe(
            direction, start_x, start_y, distance, duration
        )

    def scroll_to_element(
        self, identifier: str, max_scrolls: int, direction: str
    ) -> Result[dict]:
        return self._accessibility_datasource.scroll_to_element(
            identifier, max_scrolls, direction
        )

    def long_press(self, identifier: str, duration: float) -> Result[None]:
        return self._accessibility_datasource.long_press(identifier, duration)

    def long_press_coordinates(
        self, x: float, y: float, duration: float
    ) -> Result[None]:
        return self._accessibility_datasource.long_press_coordinates(x, y, duration)

    # =========================================================================
    # ASSERTIONS
    # =========================================================================

    def assert_element_exists(self, identifier: str) -> Result[None]:
        return self._accessibility_datasource.assert_element_exists(identifier)

    def assert_element_not_exists(self, identifier: str) -> Result[None]:
        return self._accessibility_datasource.assert_element_not_exists(identifier)

    def assert_element_visible(self, identifier: str) -> Result[None]:
        return self._accessibility_datasource.assert_element_visible(identifier)

    def assert_element_enabled(self, identifier: str) -> Result[None]:
        return self._accessibility_datasource.assert_element_enabled(identifier)

    def assert_text_equals(self, identifier: str, expected: str) -> Result[None]:
        return self._accessibility_datasource.assert_text_equals(identifier, expected)

    def assert_text_contains(self, identifier: str, substring: str) -> Result[None]:
        return self._accessibility_datasource.assert_text_contains(identifier, substring)

    def assert_element_count(self, identifier: str, expected_count: int) -> Result[None]:
        return self._accessibility_datasource.assert_element_count(identifier, expected_count)

    # =========================================================================
    # RETRY UTILITIES
    # =========================================================================

    def tap_element_with_retry(
        self, identifier: str, retries: int, interval: float
    ) -> Result[None]:
        return self._accessibility_datasource.tap_element_with_retry(
            identifier, retries, interval
        )

    def input_text_with_retry(
        self, identifier: str, text: str, retries: int, interval: float
    ) -> Result[None]:
        return self._accessibility_datasource.input_text_with_retry(
            identifier, text, retries, interval
        )
