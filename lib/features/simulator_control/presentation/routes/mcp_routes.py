"""MCP tool registration."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.presentation.viewmodels.simulator_mcp_viewmodel import (
    SimulatorMcpViewModel,
)


def register_routes(mcp, viewmodel: SimulatorMcpViewModel) -> None:
    """Register MCP tool handlers."""

    # =========================================================================
    # CORE OPERATIONS
    # =========================================================================

    @mcp.tool()
    def list_ui_elements() -> dict:
        """Return the simulator UI tree."""
        try:
            ui_tree = viewmodel.list_ui_elements()
            return Result.success(data=ui_tree, message="UI tree fetched").to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def tap_element(identifier: str) -> dict:
        """Tap a UI element by identifier or label."""
        try:
            result = viewmodel.tap_element(identifier)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def tap_coordinates(x: float, y: float) -> dict:
        """Tap a UI element by absolute screen coordinates."""
        try:
            result = viewmodel.tap_coordinates(x, y)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def input_text(identifier: str, text: str) -> dict:
        """Input text into a UI element by identifier or label."""
        try:
            result = viewmodel.input_text(identifier, text)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def launch_app(bundle_id: str, device_id: Optional[str] = None) -> dict:
        """Launch an app on the simulator."""
        try:
            result = viewmodel.launch_app(bundle_id, device_id)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def stop_app(bundle_id: str, device_id: Optional[str] = None) -> dict:
        """Stop an app on the simulator."""
        try:
            result = viewmodel.stop_app(bundle_id, device_id)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def reset_app(bundle_id: str, device_id: Optional[str] = None) -> dict:
        """Reset an app on the simulator (terminate + uninstall)."""
        try:
            result = viewmodel.reset_app(bundle_id, device_id)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def list_simulators() -> dict:
        """List available simulator devices."""
        try:
            result = viewmodel.list_simulators()
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def take_screenshot(
        device_id: Optional[str] = None, output_path: Optional[str] = None
    ) -> dict:
        """Capture a simulator screenshot and save it to disk."""
        try:
            result = viewmodel.take_screenshot(device_id, output_path)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def handle_permission_alert(action: str = "allow") -> dict:
        """Handle a permission alert by tapping allow/deny."""
        try:
            result = viewmodel.handle_permission_alert(action)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def set_target_simulator_window(title_contains: Optional[str] = None) -> dict:
        """Target a simulator window by title substring (pass empty to clear)."""
        try:
            result = viewmodel.set_target_simulator_window(title_contains)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def allow_permission_alert() -> dict:
        """Tap the allow button on a permission alert."""
        try:
            result = viewmodel.handle_permission_alert("allow")
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def deny_permission_alert() -> dict:
        """Tap the deny button on a permission alert."""
        try:
            result = viewmodel.handle_permission_alert("deny")
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    # =========================================================================
    # WAIT UTILITIES
    # =========================================================================

    @mcp.tool()
    def wait_for_element(identifier: str, timeout: float = 10.0) -> dict:
        """Wait for an element to appear on screen.

        Args:
            identifier: Element identifier, label, or text to find
            timeout: Maximum time to wait in seconds (default: 10)

        Returns:
            Element info if found, failure if timeout
        """
        try:
            result = viewmodel.wait_for_element(identifier, timeout)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def wait_for_element_gone(identifier: str, timeout: float = 10.0) -> dict:
        """Wait for an element to disappear from screen.

        Args:
            identifier: Element identifier, label, or text
            timeout: Maximum time to wait in seconds (default: 10)

        Returns:
            Success if element gone, failure if timeout
        """
        try:
            result = viewmodel.wait_for_element_gone(identifier, timeout)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def wait_for_text(text: str, timeout: float = 10.0) -> dict:
        """Wait for specific text to appear anywhere on screen.

        Args:
            text: Text to search for
            timeout: Maximum time to wait in seconds (default: 10)

        Returns:
            Element info containing the text if found
        """
        try:
            result = viewmodel.wait_for_text(text, timeout)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    # =========================================================================
    # ELEMENT STATE CHECKS
    # =========================================================================

    @mcp.tool()
    def is_element_visible(identifier: str) -> dict:
        """Check if an element is visible on screen.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            True if visible, False otherwise
        """
        try:
            result = viewmodel.is_element_visible(identifier)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def is_element_enabled(identifier: str) -> dict:
        """Check if an element is enabled (not disabled).

        Args:
            identifier: Element identifier, label, or text

        Returns:
            True if enabled, False otherwise
        """
        try:
            result = viewmodel.is_element_enabled(identifier)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def get_element_text(identifier: str) -> dict:
        """Get the text content of an element.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Element's text content
        """
        try:
            result = viewmodel.get_element_text(identifier)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def get_element_attribute(identifier: str, attribute: str) -> dict:
        """Get a specific attribute from an element.

        Args:
            identifier: Element identifier, label, or text
            attribute: Accessibility attribute name (e.g., 'AXRole', 'AXValue')

        Returns:
            Attribute value
        """
        try:
            result = viewmodel.get_element_attribute(identifier, attribute)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def get_element_count(identifier: str) -> dict:
        """Count elements matching the identifier.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Number of matching elements
        """
        try:
            result = viewmodel.get_element_count(identifier)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    # =========================================================================
    # GESTURE SUPPORT
    # =========================================================================

    @mcp.tool()
    def swipe(
        direction: str,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None,
        distance: float = 300.0,
        duration: float = 0.3,
    ) -> dict:
        """Perform a swipe gesture.

        Args:
            direction: 'up', 'down', 'left', or 'right'
            start_x: Starting X coordinate (defaults to screen center)
            start_y: Starting Y coordinate (defaults to screen center)
            distance: Swipe distance in pixels (default: 300)
            duration: Swipe duration in seconds (default: 0.3)

        Returns:
            Success or failure result
        """
        try:
            result = viewmodel.swipe(direction, start_x, start_y, distance, duration)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def scroll_to_element(
        identifier: str,
        max_scrolls: int = 10,
        direction: str = "down",
    ) -> dict:
        """Scroll until an element becomes visible.

        Args:
            identifier: Element identifier to scroll to
            max_scrolls: Maximum number of scroll attempts (default: 10)
            direction: Scroll direction - 'down' or 'up' (default: 'down')

        Returns:
            Element info if found, failure if not found after max scrolls
        """
        try:
            result = viewmodel.scroll_to_element(identifier, max_scrolls, direction)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def long_press(identifier: str, duration: float = 1.0) -> dict:
        """Perform a long press on an element.

        Args:
            identifier: Element identifier, label, or text
            duration: Press duration in seconds (default: 1.0)

        Returns:
            Success or failure result
        """
        try:
            result = viewmodel.long_press(identifier, duration)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def long_press_coordinates(x: float, y: float, duration: float = 1.0) -> dict:
        """Perform a long press at specific coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds (default: 1.0)

        Returns:
            Success or failure result
        """
        try:
            result = viewmodel.long_press_coordinates(x, y, duration)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    # =========================================================================
    # ASSERTIONS
    # =========================================================================

    @mcp.tool()
    def assert_element_exists(identifier: str) -> dict:
        """Assert that an element exists on screen.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Success if exists, failure if not
        """
        try:
            result = viewmodel.assert_element_exists(identifier)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def assert_element_not_exists(identifier: str) -> dict:
        """Assert that an element does NOT exist on screen.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Success if not exists, failure if exists
        """
        try:
            result = viewmodel.assert_element_not_exists(identifier)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def assert_element_visible(identifier: str) -> dict:
        """Assert that an element is visible on screen.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Success if visible, failure if not
        """
        try:
            result = viewmodel.assert_element_visible(identifier)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def assert_element_enabled(identifier: str) -> dict:
        """Assert that an element is enabled.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Success if enabled, failure if not
        """
        try:
            result = viewmodel.assert_element_enabled(identifier)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def assert_text_equals(identifier: str, expected: str) -> dict:
        """Assert that an element's text equals expected value.

        Args:
            identifier: Element identifier, label, or text
            expected: Expected text value

        Returns:
            Success if text matches, failure if not
        """
        try:
            result = viewmodel.assert_text_equals(identifier, expected)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def assert_text_contains(identifier: str, substring: str) -> dict:
        """Assert that an element's text contains a substring.

        Args:
            identifier: Element identifier, label, or text
            substring: Expected substring

        Returns:
            Success if text contains substring, failure if not
        """
        try:
            result = viewmodel.assert_text_contains(identifier, substring)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def assert_element_count(identifier: str, expected_count: int) -> dict:
        """Assert the count of elements matching an identifier.

        Args:
            identifier: Element identifier, label, or text
            expected_count: Expected number of matching elements

        Returns:
            Success if count matches, failure if not
        """
        try:
            result = viewmodel.assert_element_count(identifier, expected_count)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    # =========================================================================
    # RETRY UTILITIES
    # =========================================================================

    @mcp.tool()
    def tap_with_retry(
        identifier: str,
        retries: int = 3,
        interval: float = 0.5,
    ) -> dict:
        """Tap an element with automatic retry on failure.

        Args:
            identifier: Element identifier, label, or text
            retries: Maximum number of retry attempts (default: 3)
            interval: Delay between retries in seconds (default: 0.5)

        Returns:
            Success or failure result
        """
        try:
            result = viewmodel.tap_with_retry(identifier, retries, interval)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()

    @mcp.tool()
    def input_text_with_retry(
        identifier: str,
        text: str,
        retries: int = 3,
        interval: float = 0.5,
    ) -> dict:
        """Input text with automatic retry on failure.

        Args:
            identifier: Element identifier, label, or text
            text: Text to input
            retries: Maximum number of retry attempts (default: 3)
            interval: Delay between retries in seconds (default: 0.5)

        Returns:
            Success or failure result
        """
        try:
            result = viewmodel.input_text_with_retry(identifier, text, retries, interval)
            return result.to_dict()
        except Exception as error:
            return Result.failure(str(error)).to_dict()
