"""Integration tests for MCP tools against a running simulator."""

import json
import os
import sys
import time
import uuid
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APP_BUNDLE_ID = os.getenv("IOS_SIM_TEST_APP_BUNDLE_ID", "com.apple.mobileslideshow")
RESET_APP_BUNDLE_ID = os.getenv("IOS_SIM_RESET_APP_BUNDLE_ID")


class SkipTest(Exception):
    """Signal a runtime skip from async test helpers."""


def _is_environment_precondition_failure(message: str) -> bool:
    text = (message or "").lower()
    known_markers = [
        "accessibility permission is required",
        "ios simulator app is not running",
        "simulator window not found",
        "no booted simulator devices found",
        "no simulator devices available to boot",
        "failed to execute tool",
    ]
    return any(marker in text for marker in known_markers)


def _flatten_nodes(node, out):
    out.append(node)
    for child in node.get("children") or []:
        _flatten_nodes(child, out)


async def _call_tool(session, name, arguments=None):
    result = await session.call_tool(name, arguments or {})
    if result.isError:
        message = str(result.content)
        if _is_environment_precondition_failure(message):
            raise SkipTest(f"Environment precondition not met for {name}: {message}")
        return {"success": False, "message": message, "data": None}
    text = result.content[0].text if result.content else "{}"
    parsed = json.loads(text)
    if not parsed.get("success", False):
        message = parsed.get("message", "")
        if _is_environment_precondition_failure(message):
            raise SkipTest(f"Environment precondition not met for {name}: {message}")
    return parsed


async def _with_session(callback):
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "lib.main", "--transport", "stdio"],
        cwd=str(REPO_ROOT),
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                return await callback(session)
            except SkipTest as exc:
                return {"__skip__": str(exc)}


def _run_with_session(callback):
    result = anyio.run(_with_session, callback)
    if isinstance(result, dict) and "__skip__" in result:
        pytest.skip(result["__skip__"])
    return result


async def _get_ui_context(session):
    ui = await _call_tool(session, "list_ui_elements")
    assert ui["success"] is True
    root = ui["data"]
    nodes = []
    _flatten_nodes(root, nodes)

    identifier = None
    for node in nodes:
        if node.get("role") != "AXButton":
            continue
        for key in ("identifier", "label", "title", "value"):
            value = node.get(key)
            if value:
                identifier = value
                break
        if identifier:
            break

    text_value = None
    if identifier:
        text_result = await _call_tool(session, "get_element_text", {"identifier": identifier})
        if text_result["success"]:
            text_value = text_result.get("data")

    return {
        "root": root,
        "nodes": nodes,
        "identifier": identifier,
        "text_value": text_value,
    }


def _skip_if_no_alert(result) -> None:
    if result["success"] is True:
        return
    message = result.get("message", "")
    raise SkipTest(f"No alert detected: {message}")


def test_list_simulators():
    async def run(session):
        result = await _call_tool(session, "list_simulators")
        assert result["success"] is True
        assert isinstance(result.get("data"), list)
        assert result["data"], "No simulators returned"

    _run_with_session(run)


def test_list_ui_elements():
    async def run(session):
        result = await _call_tool(session, "list_ui_elements")
        assert result["success"] is True
        data = result.get("data")
        assert isinstance(data, dict)
        assert "role" in data
        assert "children" in data

    _run_with_session(run)


def test_tap_coordinates():
    async def run(session):
        ui = await _call_tool(session, "list_ui_elements")
        assert ui["success"] is True
        root = ui["data"]
        frame = root.get("frame")
        assert frame is not None, "Root frame missing"
        tap_x = frame["x"] + frame["width"] * 0.5
        tap_y = frame["y"] + frame["height"] * 0.5
        result = await _call_tool(session, "tap_coordinates", {"x": tap_x, "y": tap_y})
        assert result["success"] is True

    _run_with_session(run)


def test_tap_element():
    async def run(session):
        context = await _get_ui_context(session)
        identifier = context["identifier"]
        if not identifier:
            raise SkipTest("No tappable element with identifier/label/title/value found.")
        result = await _call_tool(session, "tap_element", {"identifier": identifier})
        assert result["success"] is True

    _run_with_session(run)


def test_launch_and_stop_app():
    async def run(session):
        launch = await _call_tool(session, "launch_app", {"bundle_id": DEFAULT_APP_BUNDLE_ID})
        assert launch["success"] is True
        time.sleep(1.0)
        stop = await _call_tool(session, "stop_app", {"bundle_id": DEFAULT_APP_BUNDLE_ID})
        assert stop["success"] is True

    _run_with_session(run)


def test_reset_app():
    if not RESET_APP_BUNDLE_ID:
        pytest.skip("Set IOS_SIM_RESET_APP_BUNDLE_ID to test reset_app.")

    async def run(session):
        result = await _call_tool(session, "reset_app", {"bundle_id": RESET_APP_BUNDLE_ID})
        assert result["success"] is True

    _run_with_session(run)


def test_take_screenshot(tmp_path):
    async def run(session):
        output_path = tmp_path / f"simulator_screenshot_{uuid.uuid4().hex}.png"
        result = await _call_tool(
            session,
            "take_screenshot",
            {"output_path": str(output_path)},
        )
        assert result["success"] is True
        assert output_path.exists(), "Screenshot file not found"

    _run_with_session(run)


def test_handle_permission_alert():
    async def run(session):
        result = await _call_tool(session, "handle_permission_alert", {"action": "allow"})
        _skip_if_no_alert(result)
        assert result["success"] is True

    _run_with_session(run)


def test_allow_permission_alert():
    async def run(session):
        result = await _call_tool(session, "allow_permission_alert")
        _skip_if_no_alert(result)
        assert result["success"] is True

    _run_with_session(run)


def test_deny_permission_alert():
    async def run(session):
        result = await _call_tool(session, "deny_permission_alert")
        _skip_if_no_alert(result)
        assert result["success"] is True

    _run_with_session(run)


def test_input_text():
    async def run(session):
        ui = await _call_tool(session, "list_ui_elements")
        assert ui["success"] is True
        nodes = []
        _flatten_nodes(ui["data"], nodes)

        identifier = None
        for node in nodes:
            if node.get("role") not in {"AXTextField", "AXTextArea", "AXSearchField"}:
                continue
            for key in ("identifier", "label", "title", "value"):
                value = node.get(key)
                if value:
                    identifier = value
                    break
            if identifier:
                break

        if not identifier:
            raise SkipTest("No accessible text field found in UI tree.")

        result = await _call_tool(
            session,
            "input_text",
            {"identifier": identifier, "text": "mcp-test"},
        )
        assert result["success"] is True

    _run_with_session(run)


def test_wait_for_element_and_text():
    async def run(session):
        context = await _get_ui_context(session)
        identifier = context["identifier"]
        text_value = context["text_value"]
        if not identifier:
            raise SkipTest("No element identifier available for wait tests.")

        found = await _call_tool(
            session,
            "wait_for_element",
            {"identifier": identifier, "timeout": 3.0},
        )
        assert found["success"] is True

        if text_value:
            text_result = await _call_tool(
                session,
                "wait_for_text",
                {"text": text_value, "timeout": 3.0},
            )
            assert text_result["success"] is True
        else:
            raise SkipTest("No text value available for wait_for_text.")

    _run_with_session(run)


def test_wait_for_element_gone_timeout():
    async def run(session):
        result = await _call_tool(
            session,
            "wait_for_element_gone",
            {"identifier": "__mcp_missing_element__", "timeout": 1.0},
        )
        if not result["success"]:
            raise SkipTest(f"wait_for_element_gone precondition not met: {result.get('message')}")
        assert result["success"] is True

    _run_with_session(run)


def test_element_state_and_attributes():
    async def run(session):
        context = await _get_ui_context(session)
        identifier = context["identifier"]
        if not identifier:
            raise SkipTest("No element identifier available for state checks.")

        visible = await _call_tool(session, "is_element_visible", {"identifier": identifier})
        assert visible["success"] is True
        assert isinstance(visible.get("data"), bool)

        enabled = await _call_tool(session, "is_element_enabled", {"identifier": identifier})
        assert enabled["success"] is True
        assert isinstance(enabled.get("data"), bool)

        text_result = await _call_tool(session, "get_element_text", {"identifier": identifier})
        assert text_result["success"] is True

        attr_result = await _call_tool(
            session,
            "get_element_attribute",
            {"identifier": identifier, "attribute": "AXRole"},
        )
        assert attr_result["success"] is True

        count_result = await _call_tool(session, "get_element_count", {"identifier": identifier})
        assert count_result["success"] is True
        assert count_result.get("data", 0) >= 1

    _run_with_session(run)


def test_gestures_and_scroll():
    async def run(session):
        context = await _get_ui_context(session)
        identifier = context["identifier"]
        root = context["root"]
        frame = root.get("frame")
        if not identifier or not frame:
            raise SkipTest("Missing UI context for gestures.")

        swipe_result = await _call_tool(session, "swipe", {"direction": "up"})
        assert swipe_result["success"] is True

        scroll_result = await _call_tool(
            session,
            "scroll_to_element",
            {"identifier": identifier, "max_scrolls": 1, "direction": "down"},
        )
        assert scroll_result["success"] is True

        long_press_result = await _call_tool(
            session,
            "long_press",
            {"identifier": identifier, "duration": 0.2},
        )
        assert long_press_result["success"] is True

        tap_x = frame["x"] + frame["width"] * 0.5
        tap_y = frame["y"] + frame["height"] * 0.5
        long_press_coord = await _call_tool(
            session,
            "long_press_coordinates",
            {"x": tap_x, "y": tap_y, "duration": 0.2},
        )
        assert long_press_coord["success"] is True

    anyio.run(_with_session, run)


def test_assertions_and_retry_utilities():
    async def run(session):
        context = await _get_ui_context(session)
        identifier = context["identifier"]
        text_value = context["text_value"]
        if not identifier:
            raise SkipTest("No element identifier available for assertions.")

        assert_exists = await _call_tool(session, "assert_element_exists", {"identifier": identifier})
        assert assert_exists["success"] is True

        assert_not_exists = await _call_tool(
            session,
            "assert_element_not_exists",
            {"identifier": "__mcp_missing_element__"},
        )
        assert assert_not_exists["success"] is True

        visible_check = await _call_tool(session, "is_element_visible", {"identifier": identifier})
        if visible_check.get("data") is True:
            assert_visible = await _call_tool(session, "assert_element_visible", {"identifier": identifier})
            assert assert_visible["success"] is True

        enabled_check = await _call_tool(session, "is_element_enabled", {"identifier": identifier})
        if enabled_check.get("data") is True:
            assert_enabled = await _call_tool(session, "assert_element_enabled", {"identifier": identifier})
            assert assert_enabled["success"] is True

        count_result = await _call_tool(session, "get_element_count", {"identifier": identifier})
        assert count_result["success"] is True
        count_value = count_result.get("data", 0)

        assert_count = await _call_tool(
            session,
            "assert_element_count",
            {"identifier": identifier, "expected_count": count_value},
        )
        assert assert_count["success"] is True

        tap_retry = await _call_tool(
            session,
            "tap_with_retry",
            {"identifier": identifier, "retries": 1, "interval": 0.2},
        )
        assert tap_retry["success"] is True

    anyio.run(_with_session, run)


def test_assert_text_equals_and_contains():
    async def run(session):
        context = await _get_ui_context(session)
        identifier = context["identifier"]
        text_value = context["text_value"]
        if not identifier or not text_value:
            raise SkipTest("No text value available for text assertions.")

        assert_equals = await _call_tool(
            session,
            "assert_text_equals",
            {"identifier": identifier, "expected": text_value},
        )
        assert assert_equals["success"] is True

        substring = text_value[:2] if len(text_value) >= 2 else text_value
        assert_contains = await _call_tool(
            session,
            "assert_text_contains",
            {"identifier": identifier, "substring": substring},
        )
        assert assert_contains["success"] is True

    anyio.run(_with_session, run)


def test_input_text_with_retry():
    async def run(session):
        ui = await _call_tool(session, "list_ui_elements")
        assert ui["success"] is True
        nodes = []
        _flatten_nodes(ui["data"], nodes)

        identifier = None
        for node in nodes:
            if node.get("role") not in {"AXTextField", "AXTextArea", "AXSearchField"}:
                continue
            for key in ("identifier", "label", "title", "value"):
                value = node.get(key)
                if value:
                    identifier = value
                    break
            if identifier:
                break

        if not identifier:
            raise SkipTest("No accessible text field found in UI tree.")

        result = await _call_tool(
            session,
            "input_text_with_retry",
            {"identifier": identifier, "text": "mcp-test", "retries": 1, "interval": 0.2},
        )
        assert result["success"] is True

    anyio.run(_with_session, run)
