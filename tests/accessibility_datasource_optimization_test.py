"""Tests for accessibility datasource matching and strict behavior."""

import time

from lib.features.simulator_control.data.datasources.accessibility_datasource import (
    AccessibilityDatasource,
)


class DummyProcessDatasource:
    """Minimal process datasource test double."""

    def __init__(self, app=None, window=None) -> None:
        self._app = app if app is not None else object()
        self._window = window if window is not None else object()

    def get_simulator_window(self):
        return self._app, self._window


def test_accessibility_permission_check_is_cached(monkeypatch):
    datasource = AccessibilityDatasource(DummyProcessDatasource())
    datasource._trust_cache_ttl_seconds = 10.0

    calls = {"count": 0}

    def fake_query():
        calls["count"] += 1
        return True

    monkeypatch.setattr(datasource, "_query_accessibility_trust", fake_query)

    datasource._ensure_accessibility_permission()
    datasource._ensure_accessibility_permission()

    assert calls["count"] == 1


def test_tap_coordinates_strict_mode_returns_failure(monkeypatch):
    datasource = AccessibilityDatasource(DummyProcessDatasource())
    datasource._strict_actions = True

    monkeypatch.setattr(datasource, "_ensure_accessibility_permission", lambda: None)
    monkeypatch.setattr(datasource, "_reset_caches", lambda: None)
    monkeypatch.setattr(
        datasource,
        "_find_pressable_element_at_position",
        lambda _app, _window, _x, _y: None,
    )

    result = datasource.tap_coordinates(10, 10)

    assert result.is_success is False
    assert "No pressable element found" in result.message


def test_tap_alert_by_coordinates_returns_false_without_pressable_targets(monkeypatch):
    datasource = AccessibilityDatasource(DummyProcessDatasource())

    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        datasource, "_get_largest_group_frame", lambda _window: (100.0, 200.0, 200.0, 100.0)
    )
    monkeypatch.setattr(
        datasource,
        "_find_pressable_element_at_position",
        lambda _app, _window, _x, _y: None,
    )

    tapped = datasource._tap_alert_by_coordinates(object(), object(), "allow")

    assert tapped is False


def test_handle_permission_alert_fails_when_button_not_pressable(monkeypatch):
    app = object()
    window = object()
    alert = object()
    button_element = object()
    datasource = AccessibilityDatasource(DummyProcessDatasource(app=app, window=window))

    monkeypatch.setattr(datasource, "_ensure_accessibility_permission", lambda: None)
    monkeypatch.setattr(datasource, "_reset_caches", lambda: None)
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    calls = {"count": 0}

    def fake_find_alert(_window, _app, deadline=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return alert
        return None

    button = {
        "element": button_element,
        "title": "allow",
        "frame": (10.0, 20.0, 30.0, 40.0),
    }

    monkeypatch.setattr(datasource, "_find_alert_container", fake_find_alert)
    monkeypatch.setattr(datasource, "_find_buttons", lambda _root, _app, deadline=None: [button])
    monkeypatch.setattr(datasource, "_select_alert_button", lambda _buttons, _action: button)
    monkeypatch.setattr(datasource, "_perform_press", lambda _element: False)
    monkeypatch.setattr(datasource, "_tap_alert_by_coordinates", lambda *_args: False)

    result = datasource.handle_permission_alert("allow")

    assert result.is_success is False
    assert "Failed to press alert button." in result.message


def test_handle_permission_alert_taps_by_coordinates_when_alert_role_missing(monkeypatch):
    datasource = AccessibilityDatasource(DummyProcessDatasource())

    monkeypatch.setattr(datasource, "_ensure_accessibility_permission", lambda: None)
    monkeypatch.setattr(datasource, "_reset_caches", lambda: None)
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    calls = {"count": 0}

    def fake_find_alert(_window, _app, deadline=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return None
        return None

    tapped = {"count": 0}

    def fake_tap_by_coordinates(_app, _window, _action):
        tapped["count"] += 1
        return True

    monkeypatch.setattr(datasource, "_find_alert_container", fake_find_alert)
    monkeypatch.setattr(datasource, "_find_buttons_fast", lambda _window: [])
    monkeypatch.setattr(datasource, "_filter_prompt_buttons", lambda _buttons, _window: [])
    monkeypatch.setattr(datasource, "_tap_alert_by_coordinates", fake_tap_by_coordinates)

    result = datasource.handle_permission_alert("allow")

    assert result.is_success is True
    assert tapped["count"] >= 1


def test_handle_permission_alert_returns_timeout_failure(monkeypatch):
    datasource = AccessibilityDatasource(DummyProcessDatasource())
    datasource._alert_handle_timeout_seconds = 0.5

    monotonic_values = iter([0.0, 1.0])
    monkeypatch.setattr(time, "monotonic", lambda: next(monotonic_values, 1.0))
    monkeypatch.setattr(datasource, "_ensure_accessibility_permission", lambda: None)
    monkeypatch.setattr(datasource, "_reset_caches", lambda: None)

    result = datasource.handle_permission_alert("allow")

    assert result.is_success is False
    assert "Timed out while handling permission alert." in result.message


def test_handle_permission_alert_uses_keyboard_fallback_without_alert_role(monkeypatch):
    datasource = AccessibilityDatasource(DummyProcessDatasource())

    monkeypatch.setattr(datasource, "_ensure_accessibility_permission", lambda: None)
    monkeypatch.setattr(datasource, "_reset_caches", lambda: None)
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(datasource, "_find_alert_container", lambda _window, _app, deadline=None: None)
    monkeypatch.setattr(
        datasource,
        "_find_buttons_fast",
        lambda _window: [{"element": object(), "frame": (886.0, 593.0, 288.0, 48.0)}],
    )
    monkeypatch.setattr(datasource, "_filter_prompt_buttons", lambda buttons, _window: buttons)
    monkeypatch.setattr(datasource, "_select_alert_button", lambda buttons, _action: buttons[0])
    monkeypatch.setattr(datasource, "_perform_press", lambda _element: False)
    monkeypatch.setattr(datasource, "_tap_alert_by_keyboard", lambda _action: True)

    result = datasource.handle_permission_alert("allow")

    assert result.is_success is True


def test_filter_prompt_buttons_excludes_hardware_like_buttons(monkeypatch):
    datasource = AccessibilityDatasource(DummyProcessDatasource())
    monkeypatch.setattr(datasource, "_get_frame", lambda _element: (802.0, 65.0, 456.0, 972.0))

    filtered = datasource._filter_prompt_buttons(
        [
            {"frame": (802.0, 347.0, 18.0, 66.0)},
            {"frame": (886.0, 593.0, 288.0, 48.0)},
            {"frame": (886.0, 649.0, 288.0, 48.0)},
        ],
        object(),
    )

    assert len(filtered) == 2


def test_tap_alert_by_keyboard_allow_uses_return_key(monkeypatch):
    datasource = AccessibilityDatasource(DummyProcessDatasource())
    pressed = []
    monkeypatch.setattr(datasource, "_press_key", lambda code: pressed.append(code) or True)

    result = datasource._tap_alert_by_keyboard("allow")

    assert result is True
    assert pressed == [36]


def test_select_alert_button_vertical_layout_prefers_top_for_allow():
    datasource = AccessibilityDatasource(DummyProcessDatasource())
    buttons = [
        {"frame": (886.0, 649.0, 288.0, 48.0), "title": None, "label": None, "value": None, "identifier": None},
        {"frame": (886.0, 593.0, 288.0, 48.0), "title": None, "label": None, "value": None, "identifier": None},
    ]

    allow_button = datasource._select_alert_button(buttons, "allow")
    deny_button = datasource._select_alert_button(buttons, "deny")

    assert allow_button["frame"][1] == 593.0
    assert deny_button["frame"][1] == 649.0


def test_find_element_prefers_exact_identifier_over_label(monkeypatch):
    root = object()
    label_match = object()
    identifier_match = object()
    datasource = AccessibilityDatasource(DummyProcessDatasource(app=root, window=root))

    children_map = {
        root: [label_match, identifier_match],
        label_match: [],
        identifier_match: [],
    }
    role_map = {
        root: "AXWindow",
        label_match: "AXButton",
        identifier_match: "AXStaticText",
    }
    frame_map = {
        label_match: (0.0, 0.0, 20.0, 20.0),
        identifier_match: (0.0, 0.0, 200.0, 200.0),
    }
    identifier_map = {
        label_match: None,
        identifier_match: "login-button",
    }
    label_map = {
        label_match: "login-button",
        identifier_match: None,
    }

    monkeypatch.setattr(datasource, "_get_children", lambda element: children_map.get(element, []))
    monkeypatch.setattr(datasource, "_get_role", lambda element: role_map.get(element))
    monkeypatch.setattr(datasource, "_get_frame", lambda element: frame_map.get(element))
    monkeypatch.setattr(
        datasource, "_get_identifier", lambda element: identifier_map.get(element)
    )
    monkeypatch.setattr(datasource, "_get_label", lambda element: label_map.get(element))
    monkeypatch.setattr(datasource, "_get_title", lambda _element: None)
    monkeypatch.setattr(datasource, "_get_value", lambda _element: None)
    monkeypatch.setattr(datasource, "_grid_scan_children", lambda *_args: [])

    result = datasource._find_element(root, root, "login-button")

    assert result is identifier_match


def test_next_poll_interval_increases_when_ui_is_stable():
    datasource = AccessibilityDatasource(DummyProcessDatasource())

    first = datasource._next_poll_interval(0.5, 0)
    second = datasource._next_poll_interval(0.5, 2)
    third = datasource._next_poll_interval(0.5, 5)

    assert first == 0.5
    assert second > first
    assert third >= second
