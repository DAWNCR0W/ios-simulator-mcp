"""Datasource for interacting with macOS Accessibility API."""

import logging
import math
import os
import re
import time
from collections import deque
from typing import List, Optional

from lib.core.constants.app_constants import (
    DEFAULT_ACCESSIBILITY_TRUST_CACHE_TTL_SECONDS,
    DEFAULT_GRID_STEP,
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_GRID_POINTS,
    DEFAULT_STRICT_ACTIONS_ENV,
)
from lib.core.errors.app_errors import AccessibilityPermissionError, SimulatorNotRunningError
from lib.core.utils.result import Result
from lib.features.simulator_control.data.models.ui_element_model import UiElementModel
from lib.features.simulator_control.data.models.ui_frame_model import UiFrameModel
from lib.features.simulator_control.data.datasources.simulator_process_datasource import (
    SimulatorProcessDatasource,
)


class AccessibilityDatasource:
    """Reads and manipulates UI elements via Accessibility APIs."""

    # Default timeouts and retry settings
    DEFAULT_TIMEOUT = 10.0
    DEFAULT_POLL_INTERVAL = 0.5
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_ALERT_HANDLE_TIMEOUT_SECONDS = 8.0

    def __init__(self, process_datasource: SimulatorProcessDatasource) -> None:
        self._process_datasource = process_datasource
        self._logger = logging.getLogger(self.__class__.__name__)
        self._grid_step = int(os.getenv("IOS_SIM_GRID_STEP", str(DEFAULT_GRID_STEP)))
        self._max_depth = int(os.getenv("IOS_SIM_MAX_DEPTH", str(DEFAULT_MAX_DEPTH)))
        self._max_grid_points = DEFAULT_MAX_GRID_POINTS
        self._strict_actions = self._resolve_bool_env(DEFAULT_STRICT_ACTIONS_ENV, False)
        self._trust_cache_ttl_seconds = float(
            os.getenv(
                "IOS_SIM_ACCESSIBILITY_TRUST_CACHE_TTL_SECONDS",
                str(DEFAULT_ACCESSIBILITY_TRUST_CACHE_TTL_SECONDS),
            )
        )
        self._alert_handle_timeout_seconds = max(
            0.5,
            float(
                os.getenv(
                    "IOS_SIM_ALERT_TIMEOUT_SECONDS",
                    str(self.DEFAULT_ALERT_HANDLE_TIMEOUT_SECONDS),
                )
            ),
        )
        self._last_trust_check_time = 0.0
        self._last_trust_check_passed = False
        self._element_counter = 0
        self._attribute_cache: dict[int, dict[str, object]] = {}
        self._frame_cache: dict[int, Optional[tuple[float, float, float, float]]] = {}
        self._children_cache: dict[int, list] = {}
        self._actions_cache: dict[int, set] = {}

    @staticmethod
    def _resolve_bool_env(name: str, default: bool) -> bool:
        raw_value = os.getenv(name)
        if raw_value is None:
            return default
        return raw_value.strip().lower() not in {"0", "false", "no", "off"}

    def _reset_caches(self) -> None:
        self._attribute_cache = {}
        self._frame_cache = {}
        self._children_cache = {}
        self._actions_cache = {}

    def get_ui_tree(self) -> UiElementModel:
        """Return the UI tree as a data model."""
        self._ensure_accessibility_permission()
        self._reset_caches()
        app_element, window_element = self._process_datasource.get_simulator_window()
        self._element_counter = 0
        visited = set()
        return self._build_tree(app_element, window_element, visited, 0)

    def tap_element(self, identifier: str) -> Result[None]:
        """Press a UI element by identifier or label."""
        self._ensure_accessibility_permission()
        self._reset_caches()
        app_element, window_element = self._process_datasource.get_simulator_window()
        target = self._find_element(app_element, window_element, identifier)
        if target is None:
            return Result.failure(f"Element not found: {identifier}")
        if not self._perform_press(target):
            return Result.failure(f"Press action failed: {identifier}")
        return Result.success(message="Tapped element")

    def tap_coordinates(self, x: float, y: float) -> Result[None]:
        """Tap an absolute screen coordinate within the simulator window."""
        self._ensure_accessibility_permission()
        self._reset_caches()
        app_element, window_element = self._process_datasource.get_simulator_window()
        target = self._find_pressable_element_at_position(app_element, window_element, x, y)
        if target is None:
            if self._strict_actions:
                return Result.failure(f"No pressable element found at coordinates ({x}, {y}).")
            return Result.success(message="Tap skipped: no element found at coordinates.")
        if not self._perform_press(target):
            if self._strict_actions:
                return Result.failure(
                    f"AXPress not supported for element at coordinates ({x}, {y})."
                )
            return Result.success(
                message="Tap skipped: AXPress not supported for element at coordinates."
            )
        return Result.success(message="Tapped coordinates via AXPress")

    def input_text(self, identifier: str, text: str) -> Result[None]:
        """Input text into a UI element by identifier or label."""
        self._ensure_accessibility_permission()
        self._reset_caches()
        app_element, window_element = self._process_datasource.get_simulator_window()
        target = self._find_element(app_element, window_element, identifier)
        if target is None:
            return Result.failure(f"Element not found: {identifier}")
        self._focus_element(target)
        if self._set_value_attribute(target, text):
            return Result.success(message="Text input applied via AXValue")
        self._type_text(text)
        return Result.success(message="Text input applied via keyboard events")

    def handle_permission_alert(self, action: str) -> Result[None]:
        """Handle a permission alert by tapping allow/deny style buttons."""
        self._ensure_accessibility_permission()
        self._reset_caches()
        action_lower = action.lower().strip()
        if action_lower not in {"allow", "deny"}:
            return Result.failure("Action must be 'allow' or 'deny'.")

        deadline = time.monotonic() + self._alert_handle_timeout_seconds
        for attempt in range(self.DEFAULT_RETRY_COUNT + 1):
            if time.monotonic() > deadline:
                return Result.failure("Timed out while handling permission alert.")
            self._reset_caches()
            app_element, window_element = self._process_datasource.get_simulator_window()
            alert_root = self._find_alert_container(window_element, app_element, deadline=deadline)
            if alert_root is None:
                fallback_buttons = self._filter_prompt_buttons(
                    self._find_buttons_fast(window_element),
                    window_element,
                )
                if fallback_buttons:
                    selected = self._select_alert_button(fallback_buttons, action_lower)
                    if selected is not None and self._perform_press(selected["element"]):
                        time.sleep(0.2)
                        continue
                    if self._tap_alert_by_keyboard(action_lower):
                        time.sleep(0.2)
                        continue
                tapped_without_alert_role = self._tap_alert_by_coordinates(
                    app_element,
                    window_element,
                    action_lower,
                )
                if tapped_without_alert_role:
                    time.sleep(0.2)
                    continue
                if attempt == 0:
                    return Result.failure("No alert detected.")
                return Result.success(message="Alert dismissed")

            buttons = self._find_buttons(alert_root, app_element, deadline=deadline)

            tapped = False
            if buttons:
                selected = self._select_alert_button(buttons, action_lower)
                if selected is not None:
                    tapped = self._perform_press(selected["element"])
                if not tapped:
                    tapped = self._tap_alert_by_coordinates(
                        app_element, window_element, action_lower
                    )
            else:
                tapped = self._tap_alert_by_coordinates(
                    app_element, window_element, action_lower
                )

            if not tapped:
                return Result.failure("Failed to press alert button.")
            time.sleep(0.2)

        app_element, window_element = self._process_datasource.get_simulator_window()
        if self._find_alert_container(window_element, app_element, deadline=deadline) is None:
            return Result.success(message="Alert dismissed")
        return Result.failure("Alert still visible after retries.")

    def set_target_window_title(self, title_substring: Optional[str]) -> Result[dict]:
        """Set the simulator window title substring to target for UI operations."""
        self._ensure_accessibility_permission()
        self._reset_caches()
        normalized = title_substring.strip() if title_substring else ""
        previous = self._process_datasource.get_target_window_title()
        self._process_datasource.set_target_window_title(normalized or None)
        if not normalized:
            return Result.success(
                data={"title_contains": None},
                message="Target window cleared",
            )
        try:
            self._process_datasource.get_simulator_window()
        except SimulatorNotRunningError as error:
            self._process_datasource.set_target_window_title(previous)
            return Result.failure(str(error))
        return Result.success(
            data={"title_contains": normalized},
            message="Target window set",
        )

    def _ensure_accessibility_permission(self) -> None:
        now = time.monotonic()
        if (
            self._last_trust_check_passed
            and self._trust_cache_ttl_seconds > 0
            and (now - self._last_trust_check_time) < self._trust_cache_ttl_seconds
        ):
            return
        is_trusted = self._query_accessibility_trust()
        self._last_trust_check_time = now
        self._last_trust_check_passed = is_trusted
        if is_trusted:
            return
        raise AccessibilityPermissionError(
            "Accessibility permission is required. Enable it in System Settings."
        )

    def _query_accessibility_trust(self) -> bool:
        try:
            from Quartz import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
        except ImportError:
            from ApplicationServices import (
                AXIsProcessTrustedWithOptions,
                kAXTrustedCheckOptionPrompt,
            )

        options = {kAXTrustedCheckOptionPrompt: True}
        return bool(AXIsProcessTrustedWithOptions(options))

    def _build_tree(self, app_element, element, visited: set, depth: int) -> UiElementModel:
        if depth > self._max_depth:
            self._logger.warning("Max depth reached at %s", depth)
            return self._create_model(element, [])

        element_key = id(element)
        if element_key in visited:
            return self._create_model(element, [])
        visited.add(element_key)

        children = self._get_children(element)
        if not children and self._get_role(element) == "AXGroup":
            frame = self._get_frame(element)
            if frame is not None:
                children = self._grid_scan_children(app_element, element, frame)

        child_models: List[UiElementModel] = []
        for child in children:
            child_models.append(self._build_tree(app_element, child, visited, depth + 1))

        return self._create_model(element, child_models)

    def _create_model(
        self, element, children: List[UiElementModel]
    ) -> UiElementModel:
        self._element_counter += 1
        frame = self._get_frame(element)
        frame_model = (
            UiFrameModel(
                x=frame[0],
                y=frame[1],
                width=frame[2],
                height=frame[3],
            )
            if frame
            else None
        )
        return UiElementModel(
            element_id=self._element_counter,
            role=self._get_role(element) or "Unknown",
            title=self._get_title(element),
            label=self._get_label(element),
            identifier=self._get_identifier(element),
            value=self._get_value(element),
            frame=frame_model,
            children=children,
        )

    def _find_element(self, app_element, root_element, identifier: str):
        identifier_lower = identifier.lower().strip()
        queue = deque([root_element])
        visited = set()
        best_match = None
        best_score = 0
        while queue:
            current = queue.popleft()
            element_key = id(current)
            if element_key in visited:
                continue
            visited.add(element_key)

            score = self._match_score(current, identifier_lower)
            if score > best_score:
                best_score = score
                best_match = current
            elif score > 0 and score == best_score and best_match is not None:
                if self._is_better_match_candidate(current, best_match):
                    best_match = current

            children = self._get_children(current)
            if not children and self._get_role(current) == "AXGroup":
                frame = self._get_frame(current)
                if frame is not None:
                    children = self._grid_scan_children(app_element, current, frame)
            queue.extend(children)
        return best_match

    def _match_score(self, element, identifier_lower: str) -> int:
        if not identifier_lower:
            return 0
        values = {
            "identifier": self._get_identifier(element),
            "label": self._get_label(element),
            "title": self._get_title(element),
            "value": self._get_value(element),
        }

        best = 0
        value = values["identifier"]
        if value:
            candidate = value.lower()
            if identifier_lower == candidate:
                best = max(best, 120)
            elif candidate.startswith(identifier_lower):
                best = max(best, 95)
            elif len(identifier_lower) > 1 and identifier_lower in candidate:
                best = max(best, 90)

        for key in ("label", "title", "value"):
            value = values[key]
            if not value:
                continue
            candidate = value.lower()
            if identifier_lower == candidate:
                best = max(best, 85)
            elif candidate.startswith(identifier_lower):
                best = max(best, 70)
            elif len(identifier_lower) > 1 and identifier_lower in candidate:
                best = max(best, 65)

        if best == 0:
            return 0
        role = self._get_role(element)
        if role in {"AXButton", "AXTextField", "AXSearchField", "AXTextArea"}:
            best += 3
        return best

    def _is_better_match_candidate(self, candidate, current) -> bool:
        candidate_identifier = self._get_identifier(candidate)
        current_identifier = self._get_identifier(current)
        if candidate_identifier and not current_identifier:
            return True
        if current_identifier and not candidate_identifier:
            return False

        candidate_frame = self._get_frame(candidate)
        current_frame = self._get_frame(current)
        if candidate_frame is None or current_frame is None:
            return candidate_frame is not None

        candidate_area = candidate_frame[2] * candidate_frame[3]
        current_area = current_frame[2] * current_frame[3]
        return candidate_area < current_area

    def _matches_identifier(self, element, identifier: str) -> bool:
        return self._match_score(element, identifier.lower().strip()) > 0

    def _get_children(self, element) -> list:
        element_key = id(element)
        cached = self._children_cache.get(element_key)
        if cached is not None:
            return cached
        try:
            from Quartz import (
                AXUIElementCopyAttributeValue,
                kAXChildrenAttribute,
                kAXErrorSuccess,
            )
        except ImportError:
            from ApplicationServices import (
                AXUIElementCopyAttributeValue,
                kAXChildrenAttribute,
                kAXErrorSuccess,
            )

        error, value = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
        if error != kAXErrorSuccess or value is None:
            self._children_cache[element_key] = []
            return []
        children = list(value)
        self._children_cache[element_key] = children
        return children

    def _get_role(self, element) -> Optional[str]:
        return self._get_string_attribute(element, "AXRole")

    def _get_title(self, element) -> Optional[str]:
        return self._get_string_attribute(element, "AXTitle")

    def _get_label(self, element) -> Optional[str]:
        return self._get_string_attribute(element, "AXLabel")

    def _get_identifier(self, element) -> Optional[str]:
        return self._get_string_attribute(element, "AXIdentifier")

    def _get_subrole(self, element) -> Optional[str]:
        return self._get_string_attribute(element, "AXSubrole")

    def _get_value(self, element) -> Optional[str]:
        value = self._get_attribute(element, "AXValue")
        if isinstance(value, str):
            return value
        if value is None:
            return None
        return str(value)

    def _get_frame(self, element) -> Optional[tuple[float, float, float, float]]:
        element_key = id(element)
        if element_key in self._frame_cache:
            return self._frame_cache[element_key]
        try:
            from Quartz import AXValueGetValue, kAXValueCGRectType
        except ImportError:
            from ApplicationServices import AXValueGetValue, kAXValueCGRectType

        ax_value = self._get_attribute(element, "AXFrame")
        if ax_value is None:
            self._frame_cache[element_key] = None
            return None
        try:
            try:
                from Quartz import CGRect
            except ImportError:
                from ApplicationServices import CGRect

            rect = CGRect()
            if AXValueGetValue(ax_value, kAXValueCGRectType, rect):
                frame = (rect.origin.x, rect.origin.y, rect.size.width, rect.size.height)
                self._frame_cache[element_key] = frame
                return frame
        except Exception as error:
            self._logger.debug("AXValueGetValue failed: %s", error)

        parsed = self._parse_frame_from_axvalue(ax_value)
        self._frame_cache[element_key] = parsed
        return parsed

    def _parse_frame_from_axvalue(self, ax_value) -> Optional[tuple[float, float, float, float]]:
        text = str(ax_value)
        match = re.search(
            r"x:(-?\d+(?:\.\d+)?)\s+y:(-?\d+(?:\.\d+)?)\s+w:(-?\d+(?:\.\d+)?)\s+h:(-?\d+(?:\.\d+)?)",
            text,
        )
        if not match:
            return None
        return tuple(float(value) for value in match.groups())

    def _get_string_attribute(self, element, attribute: str) -> Optional[str]:
        value = self._get_attribute(element, attribute)
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)

    def _get_attribute(self, element, attribute: str):
        element_key = id(element)
        cached_attrs = self._attribute_cache.setdefault(element_key, {})
        if attribute in cached_attrs:
            return cached_attrs[attribute]
        try:
            from Quartz import AXUIElementCopyAttributeValue, kAXErrorSuccess
        except ImportError:
            from ApplicationServices import AXUIElementCopyAttributeValue, kAXErrorSuccess

        error, value = AXUIElementCopyAttributeValue(element, attribute, None)
        if error != kAXErrorSuccess:
            cached_attrs[attribute] = None
            return None
        cached_attrs[attribute] = value
        return value

    def _grid_scan_children(self, app_element, parent_element, frame) -> list:
        width = max(frame[2], 0)
        height = max(frame[3], 0)
        if width == 0 or height == 0:
            return []

        step = max(self._grid_step, 5)
        max_points = self._max_grid_points
        points_scanned = 0
        children = []
        signatures = set()

        area = width * height
        if max_points > 0 and area > 0:
            desired_step = int(math.sqrt(area / max_points))
            if desired_step > step:
                step = desired_step
        step = max(step, 5)

        x = frame[0]
        while x <= frame[0] + width and points_scanned < max_points:
            y = frame[1]
            while y <= frame[1] + height and points_scanned < max_points:
                element = self._element_at_position(app_element, x, y)
                points_scanned += 1
                if element is not None and element is not parent_element:
                    signature = self._element_signature(element)
                    if signature not in signatures:
                        signatures.add(signature)
                        children.append(element)
                y += step
            x += step
        return children

    def _element_at_position(self, app_element, x: float, y: float):
        try:
            from Quartz import AXUIElementCopyElementAtPosition, kAXErrorSuccess
        except ImportError:
            from ApplicationServices import AXUIElementCopyElementAtPosition, kAXErrorSuccess

        error, element = AXUIElementCopyElementAtPosition(app_element, x, y, None)
        if error != kAXErrorSuccess:
            return None
        return element

    def _element_signature(self, element) -> str:
        role = self._get_role(element) or ""
        identifier = self._get_identifier(element) or ""
        label = self._get_label(element) or ""
        title = self._get_title(element) or ""
        frame = self._get_frame(element)
        frame_key = "" if frame is None else f"{frame[0]}:{frame[1]}:{frame[2]}:{frame[3]}"
        return f"{role}|{identifier}|{label}|{title}|{frame_key}"

    def _get_actions(self, element) -> set:
        element_key = id(element)
        cached = self._actions_cache.get(element_key)
        if cached is not None:
            return cached
        try:
            from Quartz import AXUIElementCopyActionNames, kAXErrorSuccess
        except ImportError:
            from ApplicationServices import AXUIElementCopyActionNames, kAXErrorSuccess

        error, actions = AXUIElementCopyActionNames(element, None)
        if error != kAXErrorSuccess or actions is None:
            self._actions_cache[element_key] = set()
            return set()
        actions_set = set(actions)
        self._actions_cache[element_key] = actions_set
        return actions_set

    def _scroll_action_name(self, direction: str):
        direction_lower = direction.lower()
        try:
            from Quartz import (
                kAXScrollDownAction,
                kAXScrollLeftAction,
                kAXScrollRightAction,
                kAXScrollUpAction,
            )
            action_map = {
                "up": kAXScrollUpAction,
                "down": kAXScrollDownAction,
                "left": kAXScrollLeftAction,
                "right": kAXScrollRightAction,
            }
        except ImportError:
            action_map = {
                "up": "AXScrollUp",
                "down": "AXScrollDown",
                "left": "AXScrollLeft",
                "right": "AXScrollRight",
            }
        return action_map.get(direction_lower)

    def _frame_contains(self, frame, x: float, y: float) -> bool:
        return (
            frame[0] <= x <= frame[0] + frame[2]
            and frame[1] <= y <= frame[1] + frame[3]
        )

    def _find_scrollable_element(
        self, app_element, root_element, x: float, y: float, direction: str
    ):
        action_name = self._scroll_action_name(direction)
        if action_name is None:
            return None

        direct = self._element_at_position(app_element, x, y)
        if direct is not None and action_name in self._get_actions(direct):
            return direct

        queue = deque([root_element])
        visited = set()
        best_element = None
        best_area = None

        while queue:
            current = queue.popleft()
            element_key = id(current)
            if element_key in visited:
                continue
            visited.add(element_key)

            frame = self._get_frame(current)
            if frame is not None and not self._frame_contains(frame, x, y):
                continue

            actions = self._get_actions(current)
            if action_name in actions and frame is not None:
                area = frame[2] * frame[3]
                if best_area is None or area < best_area:
                    best_area = area
                    best_element = current

            children = self._get_children(current)
            if children:
                queue.extend(children)

        return best_element

    def _find_pressable_element_at_position(self, app_element, root_element, x: float, y: float):
        try:
            from Quartz import kAXPressAction
        except ImportError:
            from ApplicationServices import kAXPressAction

        direct = self._element_at_position(app_element, x, y)
        if direct is not None and kAXPressAction in self._get_actions(direct):
            return direct

        queue = deque([root_element])
        visited = set()
        best_element = None
        best_area = None

        while queue:
            current = queue.popleft()
            element_key = id(current)
            if element_key in visited:
                continue
            visited.add(element_key)

            frame = self._get_frame(current)
            if frame is not None and not self._frame_contains(frame, x, y):
                continue

            actions = self._get_actions(current)
            if kAXPressAction in actions and frame is not None:
                area = frame[2] * frame[3]
                if best_area is None or area < best_area:
                    best_area = area
                    best_element = current

            children = self._get_children(current)
            if children:
                queue.extend(children)

        return best_element

    def _perform_press(self, element) -> bool:
        try:
            from Quartz import AXUIElementPerformAction, kAXErrorSuccess, kAXPressAction
        except ImportError:
            from ApplicationServices import (
                AXUIElementPerformAction,
                kAXErrorSuccess,
                kAXPressAction,
            )

        actions = self._get_actions(element)
        if kAXPressAction not in actions:
            return False
        result = AXUIElementPerformAction(element, kAXPressAction)
        return result == kAXErrorSuccess

    def _perform_scroll_action(self, element, direction: str) -> bool:
        try:
            from Quartz import AXUIElementPerformAction, kAXErrorSuccess
        except ImportError:
            from ApplicationServices import AXUIElementPerformAction, kAXErrorSuccess

        action_name = self._scroll_action_name(direction)
        if action_name is None:
            return False
        actions = self._get_actions(element)
        if action_name not in actions:
            return False
        result = AXUIElementPerformAction(element, action_name)
        return result == kAXErrorSuccess

    def _focus_element(self, element) -> None:
        try:
            from Quartz import AXUIElementPerformAction, kAXPressAction
        except ImportError:
            from ApplicationServices import AXUIElementPerformAction, kAXPressAction

        try:
            AXUIElementPerformAction(element, kAXPressAction)
        except Exception:
            self._logger.debug("Press action failed while focusing element")

    def _set_value_attribute(self, element, text: str) -> bool:
        try:
            from Quartz import AXUIElementSetAttributeValue, kAXErrorSuccess
        except ImportError:
            from ApplicationServices import AXUIElementSetAttributeValue, kAXErrorSuccess

        result = AXUIElementSetAttributeValue(element, "AXValue", text)
        return result == kAXErrorSuccess

    def _type_text(self, text: str) -> None:
        try:
            from Quartz import (
                CGEventCreateKeyboardEvent,
                CGEventKeyboardSetUnicodeString,
                CGEventPost,
                kCGHIDEventTap,
            )
        except ImportError:
            from ApplicationServices import (
                CGEventCreateKeyboardEvent,
                CGEventKeyboardSetUnicodeString,
                CGEventPost,
                kCGHIDEventTap,
            )

        for character in text:
            key_down = CGEventCreateKeyboardEvent(None, 0, True)
            CGEventKeyboardSetUnicodeString(key_down, len(character), character)
            CGEventPost(kCGHIDEventTap, key_down)
            key_up = CGEventCreateKeyboardEvent(None, 0, False)
            CGEventKeyboardSetUnicodeString(key_up, len(character), character)
            CGEventPost(kCGHIDEventTap, key_up)
            time.sleep(0.01)

    def _find_alert_container(self, root_element, app_element, deadline: Optional[float] = None):
        queue = deque([(root_element, 0)])
        visited = set()
        max_depth = min(self._max_depth, 16)
        while queue:
            if deadline is not None and time.monotonic() > deadline:
                return None
            element, depth = queue.popleft()
            if depth > max_depth:
                continue
            element_key = id(element)
            if element_key in visited:
                continue
            visited.add(element_key)
            role = self._get_role(element) or ""
            subrole = self._get_subrole(element) or ""
            if role in {"AXAlert", "AXDialog", "AXSheet"} or subrole in {
                "AXDialog",
                "AXSystemDialog",
            }:
                return element
            children = self._get_children(element)
            if not children and role == "AXGroup":
                frame = self._get_frame(element)
                if frame is not None:
                    children = self._grid_scan_children(app_element, element, frame)
            queue.extend((child, depth + 1) for child in children)
        return None

    def _find_buttons(
        self, root_element, app_element, deadline: Optional[float] = None
    ) -> list[dict]:
        queue = deque([(root_element, 0)])
        visited = set()
        buttons = []
        max_depth = min(self._max_depth, 16)
        while queue:
            if deadline is not None and time.monotonic() > deadline:
                return buttons
            element, depth = queue.popleft()
            if depth > max_depth:
                continue
            element_key = id(element)
            if element_key in visited:
                continue
            visited.add(element_key)
            role = self._get_role(element) or ""
            if role == "AXButton":
                buttons.append(
                    {
                        "element": element,
                        "title": self._get_title(element),
                        "label": self._get_label(element),
                        "identifier": self._get_identifier(element),
                        "value": self._get_value(element),
                        "frame": self._get_frame(element),
                    }
                )
            children = self._get_children(element)
            if not children and role == "AXGroup":
                frame = self._get_frame(element)
                if frame is not None:
                    children = self._grid_scan_children(app_element, element, frame)
            queue.extend((child, depth + 1) for child in children)
        return buttons

    def _find_buttons_fast(self, root_element) -> list[dict]:
        """Collect button-like nodes without expensive grid scanning."""
        queue = deque([(root_element, 0)])
        visited = set()
        buttons = []
        max_depth = min(self._max_depth, 12)
        while queue:
            element, depth = queue.popleft()
            if depth > max_depth:
                continue
            element_key = id(element)
            if element_key in visited:
                continue
            visited.add(element_key)
            role = self._get_role(element) or ""
            if role == "AXButton":
                buttons.append(
                    {
                        "element": element,
                        "title": self._get_title(element),
                        "label": self._get_label(element),
                        "identifier": self._get_identifier(element),
                        "value": self._get_value(element),
                        "frame": self._get_frame(element),
                    }
                )
            children = self._get_children(element)
            queue.extend((child, depth + 1) for child in children)
        return buttons

    def _filter_prompt_buttons(self, buttons: list[dict], window_element) -> list[dict]:
        window_frame = self._get_frame(window_element)
        if window_frame is None:
            return []

        window_x, window_y, window_w, window_h = window_frame
        min_width = max(80.0, window_w * 0.18)
        min_height = max(28.0, window_h * 0.03)
        candidates = []

        for button in buttons:
            frame = button.get("frame")
            if frame is None:
                continue
            x, y, width, height = frame
            if width < min_width or height < min_height:
                continue
            center_x = x + (width / 2.0)
            center_y = y + (height / 2.0)
            if center_x < (window_x + window_w * 0.18) or center_x > (window_x + window_w * 0.82):
                continue
            if center_y < (window_y + window_h * 0.25) or center_y > (window_y + window_h * 0.95):
                continue
            candidates.append(button)

        return candidates

    def _select_alert_button(self, buttons: list[dict], action: str) -> Optional[dict]:
        allow_labels = {
            "allow",
            "ok",
            "확인",
            "허용",
            "always allow",
            "allow once",
            "allow while using app",
            "allow while using the app",
        }
        deny_labels = {
            "don't allow",
            "don’t allow",
            "deny",
            "not now",
            "later",
            "취소",
            "허용 안 함",
            "허용하지 않음",
        }
        labels = allow_labels if action == "allow" else deny_labels

        def normalized_text(button: dict) -> str:
            for key in ("title", "label", "value", "identifier"):
                value = button.get(key)
                if value:
                    return str(value).strip().lower()
            return ""

        for button in buttons:
            text = normalized_text(button)
            if text in labels:
                return button

        # Fallback: choose by x position (rightmost for allow, leftmost for deny)
        framed = [btn for btn in buttons if btn.get("frame") is not None]
        if framed:
            x_centers = [btn["frame"][0] + (btn["frame"][2] / 2.0) for btn in framed]
            y_centers = [btn["frame"][1] + (btn["frame"][3] / 2.0) for btn in framed]
            x_span = max(x_centers) - min(x_centers)
            y_span = max(y_centers) - min(y_centers)

            # Vertical action sheets often expose no labels in AX; prefer top for allow.
            if y_span > x_span * 1.2:
                framed.sort(key=lambda btn: btn["frame"][1])
                return framed[0] if action == "allow" else framed[-1]

            framed.sort(key=lambda btn: btn["frame"][0])
            return framed[-1] if action == "allow" else framed[0]
        return buttons[0] if action == "allow" else buttons[-1]

    def _tap_alert_by_coordinates(
        self, app_element, window_element, action: str
    ) -> bool:
        content_frame = self._get_largest_group_frame(window_element)
        if content_frame is None:
            return False
        x_ratios = [0.72, 0.78] if action == "allow" else [0.28, 0.22]
        y_ratios = [0.62, 0.68, 0.72, 0.76]

        for x_ratio in x_ratios:
            for y_ratio in y_ratios:
                x = content_frame[0] + content_frame[2] * x_ratio
                y = content_frame[1] + content_frame[3] * y_ratio

                target = self._find_pressable_element_at_position(
                    app_element, window_element, x, y
                )
                if target is not None and self._perform_press(target):
                    return True
                time.sleep(0.05)

        return False

    def _tap_alert_by_keyboard(self, action: str) -> bool:
        """Fallback for dialogs that expose no pressable AX button actions."""
        if action == "allow":
            sequences = [[36], [76], [49]]
        else:
            sequences = [[53], [48, 36], [123, 36], [124, 36]]
        for sequence in sequences:
            if all(self._press_key(key_code) for key_code in sequence):
                return True
        return False

    def _press_key(self, key_code: int) -> bool:
        try:
            from Quartz import (
                CGEventCreateKeyboardEvent,
                CGEventPost,
                CGEventPostToPid,
                kCGHIDEventTap,
            )
        except ImportError:
            from ApplicationServices import (
                CGEventCreateKeyboardEvent,
                CGEventPost,
                CGEventPostToPid,
                kCGHIDEventTap,
            )

        try:
            key_down = CGEventCreateKeyboardEvent(None, key_code, True)
            key_up = CGEventCreateKeyboardEvent(None, key_code, False)
            if key_down is None or key_up is None:
                return False
            pid = None
            try:
                app, _ = self._process_datasource.get_simulator_application()
                pid = int(app.processIdentifier())
            except Exception:
                pid = None

            if pid is not None and pid > 0:
                CGEventPostToPid(pid, key_down)
                time.sleep(0.01)
                CGEventPostToPid(pid, key_up)
            else:
                CGEventPost(kCGHIDEventTap, key_down)
                time.sleep(0.01)
                CGEventPost(kCGHIDEventTap, key_up)
            return True
        except Exception as error:
            self._logger.debug("Keyboard fallback failed for key %s: %s", key_code, error)
            return False

    def _get_largest_group_frame(
        self, window_element
    ) -> Optional[tuple[float, float, float, float]]:
        queue = deque([window_element])
        visited = set()
        best = None
        while queue:
            element = queue.popleft()
            element_key = id(element)
            if element_key in visited:
                continue
            visited.add(element_key)
            role = self._get_role(element)
            frame = self._get_frame(element)
            if role == "AXGroup" and frame:
                if best is None or (frame[2] * frame[3]) > (best[2] * best[3]):
                    best = frame
            children = self._get_children(element)
            queue.extend(children)
        return best

    def _window_snapshot_signature(self, window_element) -> str:
        frame = self._get_frame(window_element)
        children_count = len(self._get_children(window_element))
        title = self._get_title(window_element) or ""
        frame_key = "" if frame is None else f"{frame[0]}:{frame[1]}:{frame[2]}:{frame[3]}"
        return f"{title}|{children_count}|{frame_key}"

    def _next_poll_interval(self, base: float, stable_iterations: int) -> float:
        if stable_iterations <= 0:
            return max(0.05, base)
        if stable_iterations <= 2:
            return min(0.6, max(0.05, base) * 1.25)
        return min(1.0, max(0.05, base) * 1.8)

    # =========================================================================
    # WAIT UTILITIES
    # =========================================================================

    def wait_for_element(
        self, identifier: str, timeout: float = DEFAULT_TIMEOUT
    ) -> Result[dict]:
        """Wait for an element to appear on screen.

        Args:
            identifier: Element identifier, label, or text to find
            timeout: Maximum time to wait in seconds

        Returns:
            Result with element info if found, failure if timeout
        """
        self._ensure_accessibility_permission()
        start_time = time.monotonic()
        deadline = start_time + max(timeout, 0.0)
        poll_interval = self.DEFAULT_POLL_INTERVAL
        last_signature = None
        stable_iterations = 0

        while time.monotonic() < deadline:
            try:
                self._reset_caches()
                app_element, window_element = self._process_datasource.get_simulator_window()
                element = self._find_element(app_element, window_element, identifier)
                if element is not None:
                    element_info = self._get_element_info(element)
                    return Result.success(
                        data=element_info,
                        message=f"Element found: {identifier}"
                    )
                signature = self._window_snapshot_signature(window_element)
                if signature == last_signature:
                    stable_iterations += 1
                else:
                    stable_iterations = 0
                    last_signature = signature
            except Exception as error:
                self._logger.debug("Error during wait_for_element: %s", error)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(self._next_poll_interval(poll_interval, stable_iterations), remaining))

        return Result.failure(f"Timeout waiting for element: {identifier} (after {timeout}s)")

    def wait_for_element_gone(
        self, identifier: str, timeout: float = DEFAULT_TIMEOUT
    ) -> Result[None]:
        """Wait for an element to disappear from screen.

        Args:
            identifier: Element identifier, label, or text
            timeout: Maximum time to wait in seconds

        Returns:
            Result success if element gone, failure if timeout
        """
        self._ensure_accessibility_permission()
        start_time = time.monotonic()
        deadline = start_time + max(timeout, 0.0)
        poll_interval = self.DEFAULT_POLL_INTERVAL
        last_signature = None
        stable_iterations = 0

        while time.monotonic() < deadline:
            try:
                self._reset_caches()
                app_element, window_element = self._process_datasource.get_simulator_window()
                element = self._find_element(app_element, window_element, identifier)
                if element is None:
                    return Result.success(message=f"Element gone: {identifier}")
                signature = self._window_snapshot_signature(window_element)
                if signature == last_signature:
                    stable_iterations += 1
                else:
                    stable_iterations = 0
                    last_signature = signature
            except Exception as error:
                self._logger.debug("Error during wait_for_element_gone: %s", error)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(self._next_poll_interval(poll_interval, stable_iterations), remaining))

        return Result.failure(f"Timeout waiting for element to disappear: {identifier} (after {timeout}s)")

    def wait_for_text(
        self, text: str, timeout: float = DEFAULT_TIMEOUT
    ) -> Result[dict]:
        """Wait for specific text to appear anywhere on screen.

        Args:
            text: Text to search for
            timeout: Maximum time to wait in seconds

        Returns:
            Result with element info containing the text if found
        """
        self._ensure_accessibility_permission()
        start_time = time.monotonic()
        deadline = start_time + max(timeout, 0.0)
        poll_interval = self.DEFAULT_POLL_INTERVAL
        last_signature = None
        stable_iterations = 0

        while time.monotonic() < deadline:
            try:
                self._reset_caches()
                app_element, window_element = self._process_datasource.get_simulator_window()
                element = self._find_element_by_text(app_element, window_element, text)
                if element is not None:
                    element_info = self._get_element_info(element)
                    return Result.success(
                        data=element_info,
                        message=f"Text found: {text}"
                    )
                signature = self._window_snapshot_signature(window_element)
                if signature == last_signature:
                    stable_iterations += 1
                else:
                    stable_iterations = 0
                    last_signature = signature
            except Exception as error:
                self._logger.debug("Error during wait_for_text: %s", error)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(self._next_poll_interval(poll_interval, stable_iterations), remaining))

        return Result.failure(f"Timeout waiting for text: {text} (after {timeout}s)")

    def _find_element_by_text(self, app_element, root_element, text: str):
        """Find element containing exact text match."""
        text_lower = text.lower().strip()
        queue = deque([root_element])
        visited = set()
        best_match = None
        best_score = 0

        while queue:
            current = queue.popleft()
            element_key = id(current)
            if element_key in visited:
                continue
            visited.add(element_key)

            score = self._match_text_score(current, text_lower)
            if score > best_score:
                best_score = score
                best_match = current
            elif score > 0 and score == best_score and best_match is not None:
                if self._is_better_match_candidate(current, best_match):
                    best_match = current

            children = self._get_children(current)
            if not children and self._get_role(current) == "AXGroup":
                frame = self._get_frame(current)
                if frame is not None:
                    children = self._grid_scan_children(app_element, current, frame)
            queue.extend(children)

        return best_match

    def _match_text_score(self, element, text_lower: str) -> int:
        if not text_lower:
            return 0
        values = [
            self._get_value(element),
            self._get_label(element),
            self._get_title(element),
        ]
        for value in values:
            if value and text_lower == value.lower():
                return 100
        for value in values:
            if value and len(text_lower) > 1 and text_lower in value.lower():
                return 70
        return 0

    def _get_element_info(self, element) -> dict:
        """Extract element info as a dictionary."""
        frame = self._get_frame(element)
        return {
            "role": self._get_role(element),
            "identifier": self._get_identifier(element),
            "label": self._get_label(element),
            "title": self._get_title(element),
            "value": self._get_value(element),
            "frame": {
                "x": frame[0],
                "y": frame[1],
                "width": frame[2],
                "height": frame[3],
            } if frame else None,
        }

    # =========================================================================
    # ELEMENT STATE CHECKS
    # =========================================================================

    def is_element_visible(self, identifier: str) -> Result[bool]:
        """Check if an element is visible on screen.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result with True if visible, False if not found or not visible
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            element = self._find_element(app_element, window_element, identifier)
            if element is None:
                return Result.success(data=False, message="Element not found")

            frame = self._get_frame(element)
            if frame is None:
                return Result.success(data=False, message="Element has no frame")

            # Check if element has positive dimensions and is on screen
            is_visible = frame[2] > 0 and frame[3] > 0 and frame[0] >= 0 and frame[1] >= 0
            return Result.success(data=is_visible, message=f"Visibility: {is_visible}")
        except Exception as error:
            return Result.failure(str(error))

    def is_element_enabled(self, identifier: str) -> Result[bool]:
        """Check if an element is enabled (not disabled).

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result with True if enabled, False if disabled or not found
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            element = self._find_element(app_element, window_element, identifier)
            if element is None:
                return Result.success(data=False, message="Element not found")

            # Check AXEnabled attribute
            enabled = self._get_attribute(element, "AXEnabled")
            if enabled is None:
                # If no AXEnabled attribute, assume enabled
                return Result.success(data=True, message="Element enabled (no AXEnabled attr)")

            return Result.success(data=bool(enabled), message=f"Enabled: {enabled}")
        except Exception as error:
            return Result.failure(str(error))

    def get_element_text(self, identifier: str) -> Result[str]:
        """Get the text content of an element.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result with element's text content
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            element = self._find_element(app_element, window_element, identifier)
            if element is None:
                return Result.failure(f"Element not found: {identifier}")

            # Try different text sources in priority order
            text = (
                self._get_value(element) or
                self._get_label(element) or
                self._get_title(element) or
                ""
            )
            return Result.success(data=text, message="Text retrieved")
        except Exception as error:
            return Result.failure(str(error))

    def get_element_attribute(self, identifier: str, attribute: str) -> Result:
        """Get a specific attribute value from an element.

        Args:
            identifier: Element identifier, label, or text
            attribute: Accessibility attribute name (e.g., 'AXRole', 'AXValue')

        Returns:
            Result with attribute value
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            element = self._find_element(app_element, window_element, identifier)
            if element is None:
                return Result.failure(f"Element not found: {identifier}")

            value = self._get_attribute(element, attribute)
            if value is None:
                return Result.success(data=None, message=f"Attribute {attribute} not found")

            # Convert to serializable format
            if isinstance(value, (str, int, float, bool)):
                return Result.success(data=value, message=f"Attribute {attribute} retrieved")
            return Result.success(data=str(value), message=f"Attribute {attribute} retrieved")
        except Exception as error:
            return Result.failure(str(error))

    def get_element_count(self, identifier: str) -> Result[int]:
        """Count elements matching the identifier.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result with count of matching elements
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            count = self._count_matching_elements(app_element, window_element, identifier)
            return Result.success(data=count, message=f"Found {count} matching elements")
        except Exception as error:
            return Result.failure(str(error))

    def _count_matching_elements(self, app_element, root_element, identifier: str) -> int:
        """Count all elements matching the identifier."""
        queue = deque([root_element])
        visited = set()
        count = 0

        while queue:
            current = queue.popleft()
            element_key = id(current)
            if element_key in visited:
                continue
            visited.add(element_key)

            if self._matches_identifier(current, identifier):
                count += 1

            children = self._get_children(current)
            if not children and self._get_role(current) == "AXGroup":
                frame = self._get_frame(current)
                if frame is not None:
                    children = self._grid_scan_children(app_element, current, frame)
            queue.extend(children)

        return count

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
        """Perform a swipe gesture.

        Args:
            direction: 'up', 'down', 'left', or 'right'
            start_x: Starting X coordinate (defaults to center)
            start_y: Starting Y coordinate (defaults to center)
            distance: Swipe distance in pixels
            duration: Swipe duration in seconds

        Returns:
            Result indicating success or failure
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            return self._swipe_internal(app_element, window_element, direction, start_x, start_y)
        except Exception as error:
            return Result.failure(str(error))

    def _swipe_internal(
        self,
        app_element,
        window_element,
        direction: str,
        start_x: Optional[float] = None,
        start_y: Optional[float] = None,
    ) -> Result[None]:
        window_frame = self._get_frame(window_element)
        if window_frame is None:
            return Result.failure("Could not get simulator window frame")

        center_x = window_frame[0] + window_frame[2] / 2
        center_y = window_frame[1] + window_frame[3] / 2
        sx = start_x if start_x is not None else center_x
        sy = start_y if start_y is not None else center_y

        direction_lower = direction.lower()
        if direction_lower not in {"up", "down", "left", "right"}:
            return Result.failure(
                f"Invalid direction: {direction}. Use 'up', 'down', 'left', or 'right'"
            )

        probe_points = [
            (sx, sy),
            (center_x, window_frame[1] + window_frame[3] * 0.4),
            (center_x, window_frame[1] + window_frame[3] * 0.6),
        ]

        for probe_x, probe_y in probe_points:
            target = self._find_scrollable_element(
                app_element, window_element, probe_x, probe_y, direction_lower
            )
            if target is not None and self._perform_scroll_action(target, direction_lower):
                return Result.success(message=f"Swiped {direction} via AX scroll action")

        if self._perform_scroll_action(window_element, direction_lower):
            return Result.success(message=f"Swiped {direction} via AX scroll action")
        if self._perform_scroll_action(app_element, direction_lower):
            return Result.success(message=f"Swiped {direction} via AX scroll action")
        if self._strict_actions:
            return Result.failure("No AX scroll actions available for swipe.")
        return Result.success(message="Swipe skipped: no AX scroll actions available.")

    def scroll_to_element(
        self,
        identifier: str,
        max_scrolls: int = 10,
        direction: str = "down",
    ) -> Result[dict]:
        """Scroll until an element becomes visible.

        Args:
            identifier: Element identifier to scroll to
            max_scrolls: Maximum number of scroll attempts
            direction: Scroll direction ('up' or 'down')

        Returns:
            Result with element info if found
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        direction_lower = direction.lower()
        if max_scrolls < 0:
            return Result.failure("max_scrolls must be >= 0")
        if direction_lower not in {"down", "up"}:
            return Result.failure("direction must be 'down' or 'up'")

        for i in range(max_scrolls):
            try:
                self._reset_caches()
                app_element, window_element = self._process_datasource.get_simulator_window()
                element = self._find_element(app_element, window_element, identifier)

                if element is not None:
                    element_info = self._get_element_info(element)
                    return Result.success(
                        data=element_info,
                        message=f"Element found after {i} scrolls"
                    )

                # Scroll in the specified direction
                scroll_result = self._swipe_internal(
                    app_element,
                    window_element,
                    direction="up" if direction_lower == "down" else "down",
                )
                if not scroll_result.is_success:
                    return Result.failure(f"Scroll failed: {scroll_result.message}")

                time.sleep(0.3)  # Wait for scroll animation
            except Exception as error:
                self._logger.debug("Error during scroll_to_element: %s", error)

        return Result.failure(f"Element not found after {max_scrolls} scrolls: {identifier}")

    def long_press(
        self,
        identifier: str,
        duration: float = 1.0,
    ) -> Result[None]:
        """Perform a long press on an element.

        Args:
            identifier: Element identifier, label, or text
            duration: Press duration in seconds

        Returns:
            Result indicating success or failure
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            element = self._find_element(app_element, window_element, identifier)
            if element is None:
                if self._strict_actions:
                    return Result.failure(f"Element not found for long press: {identifier}")
                return Result.success(message=f"Long press skipped: element not found: {identifier}")
            if not self._perform_press(element):
                if self._strict_actions:
                    return Result.failure(f"AXPress not supported for long press: {identifier}")
                return Result.success(
                    message=f"Long press skipped: AXPress not supported: {identifier}"
                )
            time.sleep(max(duration, 0.0))
            return Result.success(message=f"Long press simulated via AXPress: {identifier}")
        except Exception as error:
            return Result.failure(str(error))

    def long_press_coordinates(
        self,
        x: float,
        y: float,
        duration: float = 1.0,
    ) -> Result[None]:
        """Perform a long press at specific coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds

        Returns:
            Result indicating success or failure
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            target = self._find_pressable_element_at_position(app_element, window_element, x, y)
            if target is None:
                if self._strict_actions:
                    return Result.failure(f"No element found for long press at ({x}, {y}).")
                return Result.success(message="Long press skipped: no element at coordinates.")
            if not self._perform_press(target):
                if self._strict_actions:
                    return Result.failure(
                        f"AXPress not supported for long press at ({x}, {y})."
                    )
                return Result.success(
                    message="Long press skipped: AXPress not supported at coordinates."
                )
            time.sleep(max(duration, 0.0))
            return Result.success(message=f"Long press simulated via AXPress at ({x}, {y})")
        except Exception as error:
            return Result.failure(str(error))

    # =========================================================================
    # ASSERTIONS
    # =========================================================================

    def assert_element_exists(self, identifier: str) -> Result[None]:
        """Assert that an element exists on screen.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result success if exists, failure if not
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            element = self._find_element(app_element, window_element, identifier)

            if element is None:
                return Result.failure(f"Assertion failed: Element not found: {identifier}")

            return Result.success(message=f"Assertion passed: Element exists: {identifier}")
        except Exception as error:
            return Result.failure(f"Assertion error: {error}")

    def assert_element_not_exists(self, identifier: str) -> Result[None]:
        """Assert that an element does NOT exist on screen.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result success if not exists, failure if exists
        """
        self._ensure_accessibility_permission()
        self._reset_caches()
        try:
            app_element, window_element = self._process_datasource.get_simulator_window()
            element = self._find_element(app_element, window_element, identifier)

            if element is not None:
                return Result.failure(f"Assertion failed: Element exists but should not: {identifier}")

            return Result.success(message=f"Assertion passed: Element does not exist: {identifier}")
        except Exception as error:
            return Result.failure(f"Assertion error: {error}")

    def assert_element_visible(self, identifier: str) -> Result[None]:
        """Assert that an element is visible on screen.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result success if visible, failure if not
        """
        result = self.is_element_visible(identifier)
        if not result.is_success:
            return Result.failure(f"Assertion error: {result.message}")

        if not result.data:
            return Result.failure(f"Assertion failed: Element not visible: {identifier}")

        return Result.success(message=f"Assertion passed: Element is visible: {identifier}")

    def assert_element_enabled(self, identifier: str) -> Result[None]:
        """Assert that an element is enabled.

        Args:
            identifier: Element identifier, label, or text

        Returns:
            Result success if enabled, failure if not
        """
        result = self.is_element_enabled(identifier)
        if not result.is_success:
            return Result.failure(f"Assertion error: {result.message}")

        if not result.data:
            return Result.failure(f"Assertion failed: Element not enabled: {identifier}")

        return Result.success(message=f"Assertion passed: Element is enabled: {identifier}")

    def assert_text_equals(self, identifier: str, expected: str) -> Result[None]:
        """Assert that an element's text equals expected value.

        Args:
            identifier: Element identifier, label, or text
            expected: Expected text value

        Returns:
            Result success if text matches, failure if not
        """
        result = self.get_element_text(identifier)
        if not result.is_success:
            return Result.failure(f"Assertion error: {result.message}")

        actual = result.data
        if actual != expected:
            return Result.failure(
                f"Assertion failed: Text mismatch for '{identifier}'. "
                f"Expected: '{expected}', Actual: '{actual}'"
            )

        return Result.success(message=f"Assertion passed: Text equals '{expected}'")

    def assert_text_contains(self, identifier: str, substring: str) -> Result[None]:
        """Assert that an element's text contains a substring.

        Args:
            identifier: Element identifier, label, or text
            substring: Expected substring

        Returns:
            Result success if text contains substring, failure if not
        """
        result = self.get_element_text(identifier)
        if not result.is_success:
            return Result.failure(f"Assertion error: {result.message}")

        actual = result.data or ""
        if substring not in actual:
            return Result.failure(
                f"Assertion failed: Text does not contain '{substring}'. "
                f"Actual text: '{actual}'"
            )

        return Result.success(message=f"Assertion passed: Text contains '{substring}'")

    def assert_element_count(self, identifier: str, expected_count: int) -> Result[None]:
        """Assert the count of elements matching an identifier.

        Args:
            identifier: Element identifier, label, or text
            expected_count: Expected number of matching elements

        Returns:
            Result success if count matches, failure if not
        """
        result = self.get_element_count(identifier)
        if not result.is_success:
            return Result.failure(f"Assertion error: {result.message}")

        actual_count = result.data
        if actual_count != expected_count:
            return Result.failure(
                f"Assertion failed: Element count mismatch for '{identifier}'. "
                f"Expected: {expected_count}, Actual: {actual_count}"
            )

        return Result.success(
            message=f"Assertion passed: Element count is {expected_count}"
        )

    # =========================================================================
    # RETRY UTILITIES
    # =========================================================================

    def tap_element_with_retry(
        self,
        identifier: str,
        retries: int = DEFAULT_RETRY_COUNT,
        interval: float = DEFAULT_POLL_INTERVAL,
    ) -> Result[None]:
        """Tap an element with automatic retry on failure.

        Args:
            identifier: Element identifier, label, or text
            retries: Maximum number of retry attempts
            interval: Delay between retries in seconds

        Returns:
            Result indicating success or failure
        """
        last_error = None

        for attempt in range(retries + 1):
            result = self.tap_element(identifier)
            if result.is_success:
                if attempt > 0:
                    return Result.success(
                        message=f"Tapped element after {attempt} retries"
                    )
                return result

            last_error = result.message
            if attempt < retries:
                self._logger.debug(
                    "Tap failed (attempt %d/%d): %s",
                    attempt + 1,
                    retries + 1,
                    last_error
                )
                time.sleep(interval)

        return Result.failure(
            f"Failed to tap element after {retries + 1} attempts: {last_error}"
        )

    def input_text_with_retry(
        self,
        identifier: str,
        text: str,
        retries: int = DEFAULT_RETRY_COUNT,
        interval: float = DEFAULT_POLL_INTERVAL,
    ) -> Result[None]:
        """Input text with automatic retry on failure.

        Args:
            identifier: Element identifier, label, or text
            text: Text to input
            retries: Maximum number of retry attempts
            interval: Delay between retries in seconds

        Returns:
            Result indicating success or failure
        """
        last_error = None

        for attempt in range(retries + 1):
            result = self.input_text(identifier, text)
            if result.is_success:
                if attempt > 0:
                    return Result.success(
                        message=f"Input text after {attempt} retries"
                    )
                return result

            last_error = result.message
            if attempt < retries:
                self._logger.debug(
                    "Input failed (attempt %d/%d): %s",
                    attempt + 1,
                    retries + 1,
                    last_error
                )
                time.sleep(interval)

        return Result.failure(
            f"Failed to input text after {retries + 1} attempts: {last_error}"
        )
