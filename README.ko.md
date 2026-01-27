<p align="center">
  <img src="https://img.shields.io/badge/MCP-iOS%20Simulator-blue?style=for-the-badge" alt="MCP iOS Simulator"/>
</p>

<p align="center"><a href="README.md">English README</a></p>

<h1 align="center">iOS Simulator MCP</h1>

<p align="center">
  <strong>macOS 접근성 API로 iOS Simulator를 제어합니다</strong>
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

## 개요

**iOS Simulator MCP**는 Model Context Protocol(MCP) 서버로, macOS 접근성 API를
사용해 iOS Simulator UI를 읽고 조작합니다. UI 트리 조회, 요소/좌표 탭,
텍스트 입력, simctl 기반 앱 제어, 대기 유틸리티, 제스처, 어설션,
스크린샷 등을 제공합니다.

## 기능

- UI 트리 조회(AX 계층)
- 식별자/라벨 기반 탭 및 좌표 탭
- 텍스트 입력
- 앱 실행/종료/리셋(simctl)
- 시뮬레이터 부팅/종료, 앱 설치/제거, URL 열기(simctl)
- 시뮬레이터 클립보드 읽기/쓰기(simctl)
- 시뮬레이터 생성/삭제/초기화 및 런타임·디바이스 타입 조회(simctl)
- 앱 데이터/권한 유틸리티(앱 목록, 컨테이너, push/pull, 권한)
- 미디어 자동화(미디어 추가, 화면 녹화)
- 스크린샷 캡처(simctl)
- 권한 알림 처리(허용/거부)
- 대기 유틸리티, 상태 체크, 제스처, 어설션, 재시도 헬퍼
- 제목 문자열로 특정 Simulator 창 지정
- STDIO 및 HTTP 전송 방식 지원

## 요구 사항

- macOS(Apple Silicon 또는 Intel)
- Python 3.11+ (시스템 Python 3.9에서는 동작하지 않습니다)
- Xcode + iOS Simulator
- 서버를 실행하는 터미널/앱에 접근성 권한 부여

### 접근성 권한 부여

1. 시스템 설정 → 개인정보 보호 및 보안 → 접근성
2. 터미널 앱(Terminal/iTerm2) 또는 Python 실행 파일 추가
3. 토글 활성화

## 설치

### Homebrew

```bash
brew tap DAWNCR0W/ios-simulator-mcp
brew install ios-simulator-mcp
```

### 소스에서 설치(개발용)

```bash
git clone https://github.com/DAWNCR0W/ios-simulator-mcp.git
cd ios-simulator-mcp

brew install python@3.11
python3.11 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

의존성 파일:

- `requirements.txt` — 런타임 의존성
- `requirements-dev.txt` — 테스트/개발 의존성

## 빠른 시작

### 1) 시뮬레이터 부팅

```bash
xcrun simctl boot "iPhone 15 Pro"
open -a Simulator
```

### 2) MCP 서버 실행

```bash
ios-simulator-mcp --transport stdio
```

또는 Python으로 직접 실행:

```bash
python3 -m lib.main --transport stdio
```

### 3) AI 클라이언트 설정

#### Claude Code

```bash
claude mcp add --transport stdio ios-simulator -- ios-simulator-mcp --transport stdio
```

프로젝트 단위 설정:

```bash
claude mcp add --transport stdio --scope project ios-simulator -- ios-simulator-mcp --transport stdio
```

#### Cursor

`~/.cursor/mcp.json`(전역) 또는 `.cursor/mcp.json`(프로젝트)에 추가:

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

#### Codex (CLI 또는 IDE 확장)

```bash
codex mcp add ios-simulator -- ios-simulator-mcp --transport stdio
```

또는 `~/.codex/config.toml`:

```toml
[mcp_servers.ios-simulator]
command = "ios-simulator-mcp"
args = ["--transport", "stdio"]
```

#### Claude Desktop (선택)

`~/Library/Application Support/Claude/claude_desktop_config.json`에 추가:

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

## API 레퍼런스

모든 도구는 다음 형태로 반환합니다:

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
- `list_runtimes()`
- `list_device_types()`
- `create_simulator(name: str, device_type_id: str, runtime_id: str)`
- `delete_simulator(device_id: str)`
- `erase_simulator(device_id: str = None, all_devices: bool = False)`
- `list_installed_apps(device_id: str = None)`
- `get_app_container(bundle_id: str, device_id: str = None, container_type: str = None)`
- `push_file(source_path: str, destination_path: str, device_id: str = None)`
- `pull_file(source_path: str, destination_path: str, device_id: str = None)`
- `set_privacy(action: str, service: str, bundle_id: str = None, device_id: str = None)`
- `add_media(media_paths: list[str], device_id: str = None)`
- `start_recording(device_id: str = None, output_path: str = None)`
- `stop_recording(device_id: str = None)`
- `boot_simulator(device_id: str = None)`
- `shutdown_simulator(device_id: str = None)`
- `install_app(app_path: str, device_id: str = None)`
- `uninstall_app(bundle_id: str, device_id: str = None)`
- `open_url(url: str, device_id: str = None)`
- `set_clipboard(text: str, device_id: str = None)`
- `get_clipboard(device_id: str = None)`
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

## 설정

환경 변수:

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `IOS_SIM_GRID_STEP` | 보조 요소 탐색 그리드 간격 | `40` |
| `IOS_SIM_MAX_DEPTH` | UI 트리 최대 탐색 깊이 | `60` |
| `IOS_SIM_LOG_LEVEL` | 로그 레벨(`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `IOS_SIM_DEVICE_ID` | simctl용 기본 디바이스 ID | 자동 감지 |
| `IOS_SIM_ACTIVATE_APP` | 작업 전 Simulator 활성화(`0`이면 포커스 강탈 없음) | `0` |

예시:

```bash
export IOS_SIM_LOG_LEVEL=DEBUG
export IOS_SIM_ACTIVATE_APP=0
ios-simulator-mcp --transport stdio
```

## 개발

```bash
pip install -r requirements-dev.txt
pytest -q -rs
```

## 라이선스

MIT
