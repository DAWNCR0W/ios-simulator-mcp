"""Tests for accessibility datasource matching and strict behavior."""

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

