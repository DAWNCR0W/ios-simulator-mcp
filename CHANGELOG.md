# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-23

### Added

#### Core Features
- **UI Tree Inspection**: `list_ui_elements()` - Retrieve the complete UI hierarchy of the iOS Simulator screen
- **Element Tapping**: `tap_element(identifier)` - Tap UI elements by accessibility identifier or label
- **Coordinate Tapping**: `tap_coordinates(x, y)` - Tap at specific screen coordinates
- **Text Input**: `input_text(identifier, text)` - Input text into text fields
- **App Launch**: `launch_app(bundle_id, device_id?)` - Launch apps in the simulator
- **App Termination**: `stop_app(bundle_id, device_id?)` - Terminate running apps
- **App Reset**: `reset_app(bundle_id, device_id?)` - Terminate and uninstall apps
- **Simulator Listing**: `list_simulators()` - List all available simulator devices
- **Screenshot Capture**: `take_screenshot(device_id?, output_path?)` - Capture simulator screenshots
- **Permission Handling**: `handle_permission_alert(action?)` - Handle system permission dialogs

#### Wait Utilities (Playwright-style)
- **Wait for Element**: `wait_for_element(identifier, timeout)` - Wait for element to appear with timeout
- **Wait for Element Gone**: `wait_for_element_gone(identifier, timeout)` - Wait for element to disappear
- **Wait for Text**: `wait_for_text(text, timeout)` - Wait for specific text to appear on screen

#### Element State Checks
- **Is Visible**: `is_element_visible(identifier)` - Check if element is visible
- **Is Enabled**: `is_element_enabled(identifier)` - Check if element is enabled
- **Get Text**: `get_element_text(identifier)` - Get element's text content
- **Get Attribute**: `get_element_attribute(identifier, attribute)` - Get specific accessibility attribute
- **Get Count**: `get_element_count(identifier)` - Count matching elements

#### Gesture Support
- **Swipe**: `swipe(direction, start_x?, start_y?, distance?, duration?)` - Perform swipe gestures
- **Scroll to Element**: `scroll_to_element(identifier, max_scrolls?, direction?)` - Scroll until element is visible
- **Long Press**: `long_press(identifier, duration?)` - Long press on element
- **Long Press Coordinates**: `long_press_coordinates(x, y, duration?)` - Long press at coordinates

#### Assertions
- **Assert Exists**: `assert_element_exists(identifier)` - Assert element exists
- **Assert Not Exists**: `assert_element_not_exists(identifier)` - Assert element does not exist
- **Assert Visible**: `assert_element_visible(identifier)` - Assert element is visible
- **Assert Enabled**: `assert_element_enabled(identifier)` - Assert element is enabled
- **Assert Text Equals**: `assert_text_equals(identifier, expected)` - Assert text matches exactly
- **Assert Text Contains**: `assert_text_contains(identifier, substring)` - Assert text contains substring
- **Assert Element Count**: `assert_element_count(identifier, expected_count)` - Assert element count

#### Retry Utilities
- **Tap with Retry**: `tap_with_retry(identifier, retries?, interval?)` - Tap with automatic retry
- **Input with Retry**: `input_text_with_retry(identifier, text, retries?, interval?)` - Input text with retry

#### Infrastructure
- **Transport Modes**: Support for both STDIO and HTTP transport
- **Clean Architecture**: Organized codebase following Clean Architecture principles
- **Environment Configuration**: Configurable via environment variables
- **Comprehensive Documentation**: Full API reference and usage guide

### Technical Details

- Built with Python 3.11+
- Uses PyObjC for macOS Accessibility API integration
- Compatible with MCP SDK (mcp>=0.3.0)
- Supports Apple Silicon and Intel Macs

---

## [Unreleased]

### Planned

- Support for landscape orientation
- Multi-touch gesture simulation
- WebView element inspection
- XCUITest integration for advanced scenarios
- Record and replay functionality
- Visual diff comparison

---

## Version History

- **1.0.0** - Initial public release with core functionality
