"""Datasource for locating and activating the iOS Simulator process."""

import os
from typing import Optional

from lib.core.constants.app_constants import DEFAULT_ACTIVATE_APP_ENV, SIMULATOR_BUNDLE_ID
from lib.core.errors.app_errors import SimulatorNotRunningError


class SimulatorProcessDatasource:
    """Finds the iOS Simulator application and its main window."""

    def __init__(self) -> None:
        self._cached_app = None
        self._should_activate_app = self._resolve_activate_flag()
        self._target_window_title = None

    def get_simulator_application(self):
        """Return the NSRunningApplication for Simulator and its AX root element."""
        app = self._find_simulator_app()
        if self._should_activate_app:
            self._activate_app(app)
        ax_element = self._create_accessibility_element(app.processIdentifier())
        return app, ax_element

    def get_simulator_window(self):
        """Return the Simulator window AX element."""
        _, app_element = self.get_simulator_application()
        if self._target_window_title:
            window = self._find_window_by_title(app_element, self._target_window_title)
            if window is None:
                raise SimulatorNotRunningError(
                    f"Simulator window not found for title: {self._target_window_title}"
                )
            return app_element, window
        window = self._get_main_window(app_element)
        return app_element, window

    def set_target_window_title(self, title_substring: Optional[str]) -> None:
        """Set a target window title substring for simulator selection."""
        normalized = title_substring.strip() if title_substring else ""
        self._target_window_title = normalized or None

    def get_target_window_title(self) -> Optional[str]:
        """Return the currently configured target window title substring."""
        return self._target_window_title

    def _find_simulator_app(self):
        if self._cached_app is not None:
            return self._cached_app

        from AppKit import NSWorkspace

        running_apps = NSWorkspace.sharedWorkspace().runningApplications()
        for app in running_apps:
            if app.bundleIdentifier() == SIMULATOR_BUNDLE_ID:
                self._cached_app = app
                return app
        raise SimulatorNotRunningError("iOS Simulator app is not running.")

    def _activate_app(self, app) -> None:
        from AppKit import NSApplicationActivateIgnoringOtherApps

        app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

    def _resolve_activate_flag(self) -> bool:
        raw_value = os.getenv(DEFAULT_ACTIVATE_APP_ENV, "0")
        return raw_value.strip().lower() not in {"0", "false", "no", "off"}

    def _create_accessibility_element(self, pid: int):
        try:
            from Quartz import AXUIElementCreateApplication
        except ImportError:
            from ApplicationServices import AXUIElementCreateApplication

        return AXUIElementCreateApplication(pid)

    def _get_main_window(self, app_element):
        try:
            from Quartz import (
                AXUIElementCopyAttributeValue,
                kAXFocusedWindowAttribute,
                kAXMainWindowAttribute,
                kAXWindowsAttribute,
            )
        except ImportError:
            from ApplicationServices import (
                AXUIElementCopyAttributeValue,
                kAXFocusedWindowAttribute,
                kAXMainWindowAttribute,
                kAXWindowsAttribute,
            )

        window = self._get_attribute(app_element, kAXFocusedWindowAttribute)
        if window is not None:
            return window
        window = self._get_attribute(app_element, kAXMainWindowAttribute)
        if window is not None:
            return window
        windows = self._get_attribute(app_element, kAXWindowsAttribute)
        if windows:
            return windows[0]
        raise SimulatorNotRunningError("Simulator window not found.")

    def _find_window_by_title(self, app_element, title_substring: str):
        try:
            from Quartz import kAXTitleAttribute, kAXWindowsAttribute
        except ImportError:
            from ApplicationServices import kAXTitleAttribute, kAXWindowsAttribute

        windows = self._get_attribute(app_element, kAXWindowsAttribute) or []
        if not windows:
            return None
        needle = title_substring.lower()
        for window in windows:
            title = self._get_attribute(window, kAXTitleAttribute)
            if not title:
                continue
            if needle in str(title).lower():
                return window
        return None

    def _get_attribute(self, element, attribute):
        try:
            from Quartz import AXUIElementCopyAttributeValue, kAXErrorSuccess
        except ImportError:
            from ApplicationServices import AXUIElementCopyAttributeValue, kAXErrorSuccess

        error, value = AXUIElementCopyAttributeValue(element, attribute, None)
        if error != kAXErrorSuccess:
            return None
        return value
