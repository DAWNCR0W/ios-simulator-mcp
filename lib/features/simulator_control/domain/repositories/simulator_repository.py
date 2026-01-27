"""Repository contract for simulator control."""

from abc import ABC, abstractmethod
from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.entities.ui_element import UiElement


class SimulatorRepository(ABC):
    """Defines the API for simulator control operations."""

    # =========================================================================
    # CORE OPERATIONS
    # =========================================================================

    @abstractmethod
    def get_ui_tree(self) -> UiElement:
        """Return the current UI tree of the simulator."""

    @abstractmethod
    def tap_element(self, identifier: str) -> Result[None]:
        """Tap an element by identifier or label."""

    @abstractmethod
    def tap_coordinates(self, x: float, y: float) -> Result[None]:
        """Tap absolute screen coordinates."""

    @abstractmethod
    def input_text(self, identifier: str, text: str) -> Result[None]:
        """Input text into a focused element."""

    @abstractmethod
    def launch_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Launch an app on the simulator."""

    @abstractmethod
    def stop_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Terminate an app on the simulator."""

    @abstractmethod
    def reset_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Reset an app on the simulator (terminate + uninstall)."""

    @abstractmethod
    def list_simulators(self) -> Result[list[dict]]:
        """List available simulator devices."""

    @abstractmethod
    def take_screenshot(
        self, device_id: Optional[str], output_path: Optional[str]
    ) -> Result[dict]:
        """Take a simulator screenshot and return file info."""

    @abstractmethod
    def list_runtimes(self) -> Result[list[dict]]:
        """List available simulator runtimes."""

    @abstractmethod
    def list_device_types(self) -> Result[list[dict]]:
        """List available simulator device types."""

    @abstractmethod
    def create_simulator(
        self, name: str, device_type_id: str, runtime_id: str
    ) -> Result[dict]:
        """Create a new simulator device."""

    @abstractmethod
    def delete_simulator(self, device_id: str) -> Result[None]:
        """Delete a simulator device by UDID."""

    @abstractmethod
    def erase_simulator(self, device_id: Optional[str], all_devices: bool) -> Result[dict]:
        """Erase simulator data for a device or all devices."""

    @abstractmethod
    def list_installed_apps(self, device_id: Optional[str]) -> Result[list[dict]]:
        """List installed apps on the simulator."""

    @abstractmethod
    def get_app_container(
        self, bundle_id: str, device_id: Optional[str], container_type: Optional[str]
    ) -> Result[dict]:
        """Get the app container path for a bundle."""

    @abstractmethod
    def push_file(self, source_path: str, destination_path: str, device_id: Optional[str]) -> Result[None]:
        """Push a file to the simulator."""

    @abstractmethod
    def pull_file(self, source_path: str, destination_path: str, device_id: Optional[str]) -> Result[None]:
        """Pull a file from the simulator."""

    @abstractmethod
    def set_privacy(
        self,
        action: str,
        service: str,
        bundle_id: Optional[str],
        device_id: Optional[str],
    ) -> Result[None]:
        """Grant/revoke/reset privacy permissions for a service."""

    @abstractmethod
    def add_media(self, media_paths: list[str], device_id: Optional[str]) -> Result[dict]:
        """Add media files to the simulator photo library."""

    @abstractmethod
    def start_recording(
        self, device_id: Optional[str], output_path: Optional[str]
    ) -> Result[dict]:
        """Start a simulator screen recording."""

    @abstractmethod
    def stop_recording(self, device_id: Optional[str]) -> Result[dict]:
        """Stop a simulator screen recording."""

    @abstractmethod
    def boot_simulator(self, device_id: Optional[str]) -> Result[dict]:
        """Boot a simulator device."""

    @abstractmethod
    def shutdown_simulator(self, device_id: Optional[str]) -> Result[dict]:
        """Shutdown a simulator device or all booted devices."""

    @abstractmethod
    def install_app(self, app_path: str, device_id: Optional[str]) -> Result[None]:
        """Install an app bundle on the simulator."""

    @abstractmethod
    def uninstall_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Uninstall an app bundle from the simulator."""

    @abstractmethod
    def open_url(self, url: str, device_id: Optional[str]) -> Result[None]:
        """Open a URL inside the simulator."""

    @abstractmethod
    def set_clipboard(self, text: str, device_id: Optional[str]) -> Result[None]:
        """Set clipboard text on the simulator."""

    @abstractmethod
    def get_clipboard(self, device_id: Optional[str]) -> Result[str]:
        """Get clipboard text from the simulator."""

    @abstractmethod
    def handle_permission_alert(self, action: str) -> Result[None]:
        """Handle system permission alerts (e.g., notifications)."""

    @abstractmethod
    def set_target_window_title(self, title_substring: Optional[str]) -> Result[dict]:
        """Set the simulator window title substring for UI targeting."""

    # =========================================================================
    # WAIT UTILITIES
    # =========================================================================

    @abstractmethod
    def wait_for_element(self, identifier: str, timeout: float) -> Result[dict]:
        """Wait for an element to appear on screen."""

    @abstractmethod
    def wait_for_element_gone(self, identifier: str, timeout: float) -> Result[None]:
        """Wait for an element to disappear from screen."""

    @abstractmethod
    def wait_for_text(self, text: str, timeout: float) -> Result[dict]:
        """Wait for specific text to appear on screen."""

    # =========================================================================
    # ELEMENT STATE CHECKS
    # =========================================================================

    @abstractmethod
    def is_element_visible(self, identifier: str) -> Result[bool]:
        """Check if an element is visible on screen."""

    @abstractmethod
    def is_element_enabled(self, identifier: str) -> Result[bool]:
        """Check if an element is enabled."""

    @abstractmethod
    def get_element_text(self, identifier: str) -> Result[str]:
        """Get the text content of an element."""

    @abstractmethod
    def get_element_attribute(self, identifier: str, attribute: str) -> Result:
        """Get a specific attribute from an element."""

    @abstractmethod
    def get_element_count(self, identifier: str) -> Result[int]:
        """Count elements matching the identifier."""

    # =========================================================================
    # GESTURE SUPPORT
    # =========================================================================

    @abstractmethod
    def swipe(
        self,
        direction: str,
        start_x: Optional[float],
        start_y: Optional[float],
        distance: float,
        duration: float,
    ) -> Result[None]:
        """Perform a swipe gesture."""

    @abstractmethod
    def scroll_to_element(
        self, identifier: str, max_scrolls: int, direction: str
    ) -> Result[dict]:
        """Scroll until an element becomes visible."""

    @abstractmethod
    def long_press(self, identifier: str, duration: float) -> Result[None]:
        """Perform a long press on an element."""

    @abstractmethod
    def long_press_coordinates(
        self, x: float, y: float, duration: float
    ) -> Result[None]:
        """Perform a long press at coordinates."""

    # =========================================================================
    # ASSERTIONS
    # =========================================================================

    @abstractmethod
    def assert_element_exists(self, identifier: str) -> Result[None]:
        """Assert that an element exists."""

    @abstractmethod
    def assert_element_not_exists(self, identifier: str) -> Result[None]:
        """Assert that an element does not exist."""

    @abstractmethod
    def assert_element_visible(self, identifier: str) -> Result[None]:
        """Assert that an element is visible."""

    @abstractmethod
    def assert_element_enabled(self, identifier: str) -> Result[None]:
        """Assert that an element is enabled."""

    @abstractmethod
    def assert_text_equals(self, identifier: str, expected: str) -> Result[None]:
        """Assert that element text equals expected value."""

    @abstractmethod
    def assert_text_contains(self, identifier: str, substring: str) -> Result[None]:
        """Assert that element text contains substring."""

    @abstractmethod
    def assert_element_count(self, identifier: str, expected_count: int) -> Result[None]:
        """Assert the count of matching elements."""

    # =========================================================================
    # RETRY UTILITIES
    # =========================================================================

    @abstractmethod
    def tap_element_with_retry(
        self, identifier: str, retries: int, interval: float
    ) -> Result[None]:
        """Tap an element with automatic retry."""

    @abstractmethod
    def input_text_with_retry(
        self, identifier: str, text: str, retries: int, interval: float
    ) -> Result[None]:
        """Input text with automatic retry."""
