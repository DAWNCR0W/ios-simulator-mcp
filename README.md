<p align="center">
  <img src="https://img.shields.io/badge/MCP-iOS%20Simulator-blue?style=for-the-badge" alt="MCP iOS Simulator"/>
</p>

<p align="center"><a href="README.ko.md">한국어 README</a></p>
<p align="center">Latest release: v1.0.0</p>

<h1 align="center">iOS Simulator MCP</h1>

<p align="center">
  <strong>Control iOS Simulator via macOS Accessibility APIs</strong>
</p>

<p align="center">
  <a href="https://github.com/anthropics/model-context-protocol">
    <img src="https://img.shields.io/badge/MCP-Compatible-green?style=flat-square" alt="MCP Compatible"/>
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"/>
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-square" alt="Python 3.11+"/>
  </a>
</p>

---

## Overview

**iOS Simulator MCP** is a Model Context Protocol (MCP) server that lets AI agents
inspect and operate iOS Simulator UI via macOS Accessibility APIs. It supports
UI tree inspection, element/coordinate interactions, app lifecycle via simctl,
wait utilities, gestures, assertions, and screenshots.

## Features

- UI tree inspection (AX hierarchy)
- Tap elements by identifier/label and tap by coordinates
- Text input into fields
- Launch/stop/reset apps (simctl)
- Screenshot capture (simctl)
- Permission alert handling (allow/deny)
- Wait utilities, state checks, gestures, assertions, retry helpers
- Target a specific Simulator window by title substring
- STDIO and HTTP transport

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.11+ (system Python 3.9 will not work)
- Xcode + iOS Simulator
- Accessibility permissions for the terminal/app running the server

### Grant Accessibility Permissions

1. System Settings → Privacy & Security → Accessibility
2. Add your terminal app (Terminal/iTerm2) or the Python executable
3. Enable the toggle

## Installation

### Homebrew

```bash
brew tap DAWNCR0W/ios-simulator-mcp
brew install ios-simulator-mcp
```

### From Source (Development)

```bash
git clone https://github.com/DAWNCR0W/ios-simulator-mcp.git
cd ios-simulator-mcp

brew install python@3.11
python3.11 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

Dependency files:

- `requirements.txt` — runtime dependencies
- `requirements-dev.txt` — test/dev dependencies

## Quick Start

### 1) Boot a Simulator

```bash
xcrun simctl boot "iPhone 15 Pro"
open -a Simulator
```

### 2) Run the MCP Server

```bash
ios-simulator-mcp --transport stdio
```

Or run directly with Python:

```bash
python3 -m lib.main --transport stdio
```

### 3) Configure Your AI Client

#### Claude Code

```bash
claude mcp add --transport stdio ios-simulator -- ios-simulator-mcp --transport stdio
```

Project scope:

```bash
claude mcp add --transport stdio --scope project ios-simulator -- ios-simulator-mcp --transport stdio
```

#### Cursor

Create `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "ios-simulator": {
      "type": "stdio",
      "command": "ios-simulator-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

#### Codex (CLI or IDE extension)

```bash
codex mcp add ios-simulator -- ios-simulator-mcp --transport stdio
```

Or edit `~/.codex/config.toml`:

```toml
[mcp_servers.ios-simulator]
command = "ios-simulator-mcp"
args = ["--transport", "stdio"]
```

#### Claude Desktop (optional)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ios-simulator": {
      "command": "ios-simulator-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

## API Reference

All tools return:

```json
{
  "success": true,
  "message": "Operation completed",
  "data": { }
}
```

### Core Operations

- `list_ui_elements()`
- `tap_element(identifier: str)`
- `tap_coordinates(x: float, y: float)`
- `input_text(identifier: str, text: str)`
- `launch_app(bundle_id: str, device_id: str = None)`
- `stop_app(bundle_id: str, device_id: str = None)`
- `reset_app(bundle_id: str, device_id: str = None)`
- `list_simulators()`
- `take_screenshot(device_id: str = None, output_path: str = None)`
- `handle_permission_alert(action: str = "allow")`
- `allow_permission_alert()`
- `deny_permission_alert()`
- `set_target_simulator_window(title_contains: str = None)`

### Wait Utilities

- `wait_for_element(identifier: str, timeout: float = 10.0)`
- `wait_for_element_gone(identifier: str, timeout: float = 10.0)`
- `wait_for_text(text: str, timeout: float = 10.0)`

### Element State Checks

- `is_element_visible(identifier: str)`
- `is_element_enabled(identifier: str)`
- `get_element_text(identifier: str)`
- `get_element_attribute(identifier: str, attribute: str)`
- `get_element_count(identifier: str)`

### Gestures

- `swipe(direction: str, start_x: float = None, start_y: float = None, distance: float = 200.0, duration: float = 0.2)`
- `scroll_to_element(identifier: str, max_scrolls: int = 10, direction: str = "down")`
- `long_press(identifier: str, duration: float = 1.0)`
- `long_press_coordinates(x: float, y: float, duration: float = 1.0)`

### Assertions

- `assert_element_exists(identifier: str)`
- `assert_element_not_exists(identifier: str)`
- `assert_element_visible(identifier: str)`
- `assert_element_enabled(identifier: str)`
- `assert_text_equals(identifier: str, expected: str)`
- `assert_text_contains(identifier: str, substring: str)`
- `assert_element_count(identifier: str, expected_count: int)`

### Retry Utilities

- `tap_element_with_retry(identifier: str, retries: int = 3, interval: float = 0.5)`
- `input_text_with_retry(identifier: str, text: str, retries: int = 3, interval: float = 0.5)`

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `IOS_SIM_GRID_STEP` | Grid step size for fallback element discovery | `40` |
| `IOS_SIM_MAX_DEPTH` | Max depth for UI tree traversal | `60` |
| `IOS_SIM_LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `IOS_SIM_DEVICE_ID` | Default simulator device ID for simctl | Auto-detected |
| `IOS_SIM_ACTIVATE_APP` | Activate Simulator app before actions (`0` disables focus stealing) | `0` |

Example:

```bash
export IOS_SIM_LOG_LEVEL=DEBUG
export IOS_SIM_ACTIVATE_APP=0
ios-simulator-mcp --transport stdio
```

## Development

```bash
pip install -r requirements-dev.txt
pytest -q -rs
```

## License

MIT
