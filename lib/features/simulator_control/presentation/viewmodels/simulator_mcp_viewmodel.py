"""ViewModel bridging MCP handlers with domain use cases."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.entities.ui_element import UiElement

# Core use cases
from lib.features.simulator_control.domain.usecases.input_text_usecase import (
    InputTextUsecase,
)
from lib.features.simulator_control.domain.usecases.launch_app_usecase import (
    LaunchAppUsecase,
)
from lib.features.simulator_control.domain.usecases.list_simulators_usecase import (
    ListSimulatorsUsecase,
)
from lib.features.simulator_control.domain.usecases.list_ui_tree_usecase import (
    ListUiTreeUsecase,
)
from lib.features.simulator_control.domain.usecases.reset_app_usecase import (
    ResetAppUsecase,
)
from lib.features.simulator_control.domain.usecases.stop_app_usecase import (
    StopAppUsecase,
)
from lib.features.simulator_control.domain.usecases.tap_element_usecase import (
    TapElementUsecase,
)
from lib.features.simulator_control.domain.usecases.tap_coordinates_usecase import (
    TapCoordinatesUsecase,
)
from lib.features.simulator_control.domain.usecases.take_screenshot_usecase import (
    TakeScreenshotUsecase,
)
from lib.features.simulator_control.domain.usecases.handle_permission_alert_usecase import (
    HandlePermissionAlertUsecase,
)
from lib.features.simulator_control.domain.usecases.set_target_window_usecase import (
    SetTargetWindowUsecase,
)

# Wait use cases
from lib.features.simulator_control.domain.usecases.wait_for_element_usecase import (
    WaitForElementUsecase,
)
from lib.features.simulator_control.domain.usecases.wait_for_element_gone_usecase import (
    WaitForElementGoneUsecase,
)
from lib.features.simulator_control.domain.usecases.wait_for_text_usecase import (
    WaitForTextUsecase,
)

# Element state use cases
from lib.features.simulator_control.domain.usecases.is_element_visible_usecase import (
    IsElementVisibleUsecase,
)
from lib.features.simulator_control.domain.usecases.is_element_enabled_usecase import (
    IsElementEnabledUsecase,
)
from lib.features.simulator_control.domain.usecases.get_element_text_usecase import (
    GetElementTextUsecase,
)
from lib.features.simulator_control.domain.usecases.get_element_attribute_usecase import (
    GetElementAttributeUsecase,
)
from lib.features.simulator_control.domain.usecases.get_element_count_usecase import (
    GetElementCountUsecase,
)

# Gesture use cases
from lib.features.simulator_control.domain.usecases.swipe_usecase import (
    SwipeUsecase,
)
from lib.features.simulator_control.domain.usecases.scroll_to_element_usecase import (
    ScrollToElementUsecase,
)
from lib.features.simulator_control.domain.usecases.long_press_usecase import (
    LongPressUsecase,
)
from lib.features.simulator_control.domain.usecases.long_press_coordinates_usecase import (
    LongPressCoordinatesUsecase,
)

# Assertion use case
from lib.features.simulator_control.domain.usecases.assertions_usecase import (
    AssertionsUsecase,
)

# Retry use cases
from lib.features.simulator_control.domain.usecases.tap_with_retry_usecase import (
    TapWithRetryUsecase,
)
from lib.features.simulator_control.domain.usecases.input_text_with_retry_usecase import (
    InputTextWithRetryUsecase,
)


class SimulatorMcpViewModel:
    """Coordinates UI operations for MCP tool handlers."""

    def __init__(
        self,
        # Core use cases
        list_ui_tree_usecase: ListUiTreeUsecase,
        tap_element_usecase: TapElementUsecase,
        tap_coordinates_usecase: TapCoordinatesUsecase,
        input_text_usecase: InputTextUsecase,
        launch_app_usecase: LaunchAppUsecase,
        stop_app_usecase: StopAppUsecase,
        reset_app_usecase: ResetAppUsecase,
        list_simulators_usecase: ListSimulatorsUsecase,
        take_screenshot_usecase: TakeScreenshotUsecase,
        handle_permission_alert_usecase: HandlePermissionAlertUsecase,
        set_target_window_usecase: SetTargetWindowUsecase,
        # Wait use cases
        wait_for_element_usecase: WaitForElementUsecase,
        wait_for_element_gone_usecase: WaitForElementGoneUsecase,
        wait_for_text_usecase: WaitForTextUsecase,
        # Element state use cases
        is_element_visible_usecase: IsElementVisibleUsecase,
        is_element_enabled_usecase: IsElementEnabledUsecase,
        get_element_text_usecase: GetElementTextUsecase,
        get_element_attribute_usecase: GetElementAttributeUsecase,
        get_element_count_usecase: GetElementCountUsecase,
        # Gesture use cases
        swipe_usecase: SwipeUsecase,
        scroll_to_element_usecase: ScrollToElementUsecase,
        long_press_usecase: LongPressUsecase,
        long_press_coordinates_usecase: LongPressCoordinatesUsecase,
        # Assertion use case
        assertions_usecase: AssertionsUsecase,
        # Retry use cases
        tap_with_retry_usecase: TapWithRetryUsecase,
        input_text_with_retry_usecase: InputTextWithRetryUsecase,
    ) -> None:
        # Core
        self._list_ui_tree_usecase = list_ui_tree_usecase
        self._tap_element_usecase = tap_element_usecase
        self._tap_coordinates_usecase = tap_coordinates_usecase
        self._input_text_usecase = input_text_usecase
        self._launch_app_usecase = launch_app_usecase
        self._stop_app_usecase = stop_app_usecase
        self._reset_app_usecase = reset_app_usecase
        self._list_simulators_usecase = list_simulators_usecase
        self._take_screenshot_usecase = take_screenshot_usecase
        self._handle_permission_alert_usecase = handle_permission_alert_usecase
        self._set_target_window_usecase = set_target_window_usecase
        # Wait
        self._wait_for_element_usecase = wait_for_element_usecase
        self._wait_for_element_gone_usecase = wait_for_element_gone_usecase
        self._wait_for_text_usecase = wait_for_text_usecase
        # Element state
        self._is_element_visible_usecase = is_element_visible_usecase
        self._is_element_enabled_usecase = is_element_enabled_usecase
        self._get_element_text_usecase = get_element_text_usecase
        self._get_element_attribute_usecase = get_element_attribute_usecase
        self._get_element_count_usecase = get_element_count_usecase
        # Gesture
        self._swipe_usecase = swipe_usecase
        self._scroll_to_element_usecase = scroll_to_element_usecase
        self._long_press_usecase = long_press_usecase
        self._long_press_coordinates_usecase = long_press_coordinates_usecase
        # Assertion
        self._assertions_usecase = assertions_usecase
        # Retry
        self._tap_with_retry_usecase = tap_with_retry_usecase
        self._input_text_with_retry_usecase = input_text_with_retry_usecase

    # =========================================================================
    # CORE OPERATIONS
    # =========================================================================

    def list_ui_elements(self) -> UiElement:
        """Return the current UI tree."""
        return self._list_ui_tree_usecase.execute()

    def tap_element(self, identifier: str) -> Result[None]:
        """Tap an element by identifier or label."""
        return self._tap_element_usecase.execute(identifier)

    def tap_coordinates(self, x: float, y: float) -> Result[None]:
        """Tap an absolute screen coordinate."""
        return self._tap_coordinates_usecase.execute(x, y)

    def input_text(self, identifier: str, text: str) -> Result[None]:
        """Input text into an element."""
        return self._input_text_usecase.execute(identifier, text)

    def launch_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Launch an app on the simulator."""
        return self._launch_app_usecase.execute(bundle_id, device_id)

    def stop_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Stop an app on the simulator."""
        return self._stop_app_usecase.execute(bundle_id, device_id)

    def reset_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Reset an app on the simulator."""
        return self._reset_app_usecase.execute(bundle_id, device_id)

    def list_simulators(self) -> Result[list[dict]]:
        """List available simulators."""
        return self._list_simulators_usecase.execute()

    def take_screenshot(
        self, device_id: Optional[str], output_path: Optional[str]
    ) -> Result[dict]:
        """Take a simulator screenshot."""
        return self._take_screenshot_usecase.execute(device_id, output_path)

    def handle_permission_alert(self, action: str) -> Result[None]:
        """Handle a permission alert by action."""
        return self._handle_permission_alert_usecase.execute(action)

    def set_target_simulator_window(
        self, title_substring: Optional[str]
    ) -> Result[dict]:
        """Set a title substring to target a simulator window."""
        return self._set_target_window_usecase.execute(title_substring)

    # =========================================================================
    # WAIT UTILITIES
    # =========================================================================

    def wait_for_element(
        self, identifier: str, timeout: float = 10.0
    ) -> Result[dict]:
        """Wait for an element to appear."""
        return self._wait_for_element_usecase.execute(identifier, timeout)

    def wait_for_element_gone(
        self, identifier: str, timeout: float = 10.0
    ) -> Result[None]:
        """Wait for an element to disappear."""
        return self._wait_for_element_gone_usecase.execute(identifier, timeout)

    def wait_for_text(self, text: str, timeout: float = 10.0) -> Result[dict]:
        """Wait for specific text to appear."""
        return self._wait_for_text_usecase.execute(text, timeout)

    # =========================================================================
    # ELEMENT STATE CHECKS
    # =========================================================================

    def is_element_visible(self, identifier: str) -> Result[bool]:
        """Check if element is visible."""
        return self._is_element_visible_usecase.execute(identifier)

    def is_element_enabled(self, identifier: str) -> Result[bool]:
        """Check if element is enabled."""
        return self._is_element_enabled_usecase.execute(identifier)

    def get_element_text(self, identifier: str) -> Result[str]:
        """Get element text content."""
        return self._get_element_text_usecase.execute(identifier)

    def get_element_attribute(self, identifier: str, attribute: str) -> Result:
        """Get element attribute value."""
        return self._get_element_attribute_usecase.execute(identifier, attribute)

    def get_element_count(self, identifier: str) -> Result[int]:
        """Count matching elements."""
        return self._get_element_count_usecase.execute(identifier)

    # =========================================================================
    # GESTURE SUPPORT
    # =========================================================================

    def swipe(
        self,
        direction: str,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None,
        distance: float = 300.0,
        duration: float = 0.3,
    ) -> Result[None]:
        """Perform a swipe gesture."""
        return self._swipe_usecase.execute(direction, start_x, start_y, distance, duration)

    def scroll_to_element(
        self,
        identifier: str,
        max_scrolls: int = 10,
        direction: str = "down",
    ) -> Result[dict]:
        """Scroll until element is visible."""
        return self._scroll_to_element_usecase.execute(identifier, max_scrolls, direction)

    def long_press(self, identifier: str, duration: float = 1.0) -> Result[None]:
        """Long press on an element."""
        return self._long_press_usecase.execute(identifier, duration)

    def long_press_coordinates(
        self, x: float, y: float, duration: float = 1.0
    ) -> Result[None]:
        """Long press at coordinates."""
        return self._long_press_coordinates_usecase.execute(x, y, duration)

    # =========================================================================
    # ASSERTIONS
    # =========================================================================

    def assert_element_exists(self, identifier: str) -> Result[None]:
        """Assert element exists."""
        return self._assertions_usecase.assert_element_exists(identifier)

    def assert_element_not_exists(self, identifier: str) -> Result[None]:
        """Assert element does not exist."""
        return self._assertions_usecase.assert_element_not_exists(identifier)

    def assert_element_visible(self, identifier: str) -> Result[None]:
        """Assert element is visible."""
        return self._assertions_usecase.assert_element_visible(identifier)

    def assert_element_enabled(self, identifier: str) -> Result[None]:
        """Assert element is enabled."""
        return self._assertions_usecase.assert_element_enabled(identifier)

    def assert_text_equals(self, identifier: str, expected: str) -> Result[None]:
        """Assert element text equals expected."""
        return self._assertions_usecase.assert_text_equals(identifier, expected)

    def assert_text_contains(self, identifier: str, substring: str) -> Result[None]:
        """Assert element text contains substring."""
        return self._assertions_usecase.assert_text_contains(identifier, substring)

    def assert_element_count(self, identifier: str, expected_count: int) -> Result[None]:
        """Assert count of matching elements."""
        return self._assertions_usecase.assert_element_count(identifier, expected_count)

    # =========================================================================
    # RETRY UTILITIES
    # =========================================================================

    def tap_with_retry(
        self,
        identifier: str,
        retries: int = 3,
        interval: float = 0.5,
    ) -> Result[None]:
        """Tap element with automatic retry."""
        return self._tap_with_retry_usecase.execute(identifier, retries, interval)

    def input_text_with_retry(
        self,
        identifier: str,
        text: str,
        retries: int = 3,
        interval: float = 0.5,
    ) -> Result[None]:
        """Input text with automatic retry."""
        return self._input_text_with_retry_usecase.execute(identifier, text, retries, interval)
