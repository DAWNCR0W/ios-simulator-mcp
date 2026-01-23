"""Unit tests for simulator use cases."""

from typing import Optional

from lib.core.utils.result import Result
from lib.features.simulator_control.domain.entities.ui_element import UiElement
from lib.features.simulator_control.domain.entities.ui_frame import UiFrame
from lib.features.simulator_control.domain.repositories.simulator_repository import (
    SimulatorRepository,
)
from lib.features.simulator_control.domain.usecases.input_text_usecase import (
    InputTextUsecase,
)
from lib.features.simulator_control.domain.usecases.launch_app_usecase import (
    LaunchAppUsecase,
)
from lib.features.simulator_control.domain.usecases.list_simulators_usecase import (
    ListSimulatorsUsecase,
)
from lib.features.simulator_control.domain.usecases.list_ui_tree_usecase import (
    ListUiTreeUsecase,
)
from lib.features.simulator_control.domain.usecases.reset_app_usecase import (
    ResetAppUsecase,
)
from lib.features.simulator_control.domain.usecases.stop_app_usecase import (
    StopAppUsecase,
)
from lib.features.simulator_control.domain.usecases.tap_element_usecase import (
    TapElementUsecase,
)
from lib.features.simulator_control.domain.usecases.take_screenshot_usecase import (
    TakeScreenshotUsecase,
)
from lib.features.simulator_control.domain.usecases.handle_permission_alert_usecase import (
    HandlePermissionAlertUsecase,
)
from lib.features.simulator_control.domain.usecases.set_target_window_usecase import (
    SetTargetWindowUsecase,
)
from lib.features.simulator_control.domain.usecases.tap_coordinates_usecase import (
    TapCoordinatesUsecase,
)
from lib.features.simulator_control.domain.usecases.wait_for_element_usecase import (
    WaitForElementUsecase,
)
from lib.features.simulator_control.domain.usecases.wait_for_element_gone_usecase import (
    WaitForElementGoneUsecase,
)
from lib.features.simulator_control.domain.usecases.wait_for_text_usecase import (
    WaitForTextUsecase,
)
from lib.features.simulator_control.domain.usecases.is_element_visible_usecase import (
    IsElementVisibleUsecase,
)
from lib.features.simulator_control.domain.usecases.is_element_enabled_usecase import (
    IsElementEnabledUsecase,
)
from lib.features.simulator_control.domain.usecases.get_element_text_usecase import (
    GetElementTextUsecase,
)
from lib.features.simulator_control.domain.usecases.get_element_attribute_usecase import (
    GetElementAttributeUsecase,
)
from lib.features.simulator_control.domain.usecases.get_element_count_usecase import (
    GetElementCountUsecase,
)
from lib.features.simulator_control.domain.usecases.swipe_usecase import (
    SwipeUsecase,
)
from lib.features.simulator_control.domain.usecases.scroll_to_element_usecase import (
    ScrollToElementUsecase,
)
from lib.features.simulator_control.domain.usecases.long_press_usecase import (
    LongPressUsecase,
)
from lib.features.simulator_control.domain.usecases.long_press_coordinates_usecase import (
    LongPressCoordinatesUsecase,
)
from lib.features.simulator_control.domain.usecases.assertions_usecase import (
    AssertionsUsecase,
)
from lib.features.simulator_control.domain.usecases.tap_with_retry_usecase import (
    TapWithRetryUsecase,
)
from lib.features.simulator_control.domain.usecases.input_text_with_retry_usecase import (
    InputTextWithRetryUsecase,
)


class FakeSimulatorRepository(SimulatorRepository):
    """Fake repository for unit testing use cases."""

    def __init__(self) -> None:
        self.last_identifier = None
        self.last_text = None
        self.last_bundle_id = None
        self.last_device_id = None
        self.last_attribute = None
        self.last_expected = None
        self.last_substring = None
        self.last_expected_count = None
        self.last_direction = None
        self.last_coordinates = None
        self.last_duration = None
        self.last_timeout = None
        self.last_retries = None
        self.last_interval = None
        self.last_action = None
        self.last_window_title = None

    def get_ui_tree(self) -> UiElement:
        return UiElement(
            element_id=1,
            role="AXWindow",
            title="Root",
            label=None,
            identifier=None,
            value=None,
            frame=UiFrame(x=0, y=0, width=100, height=100),
            children=[],
        )

    def tap_element(self, identifier: str) -> Result[None]:
        self.last_identifier = identifier
        return Result.success(message="Tapped")

    def tap_coordinates(self, x: float, y: float) -> Result[None]:
        self.last_coordinates = (x, y)
        return Result.success(message="Tapped coordinates")

    def input_text(self, identifier: str, text: str) -> Result[None]:
        self.last_identifier = identifier
        self.last_text = text
        return Result.success(message="Input")

    def launch_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        self.last_bundle_id = bundle_id
        self.last_device_id = device_id
        return Result.success(message="Launched")

    def stop_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        self.last_bundle_id = bundle_id
        self.last_device_id = device_id
        return Result.success(message="Stopped")

    def reset_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        self.last_bundle_id = bundle_id
        self.last_device_id = device_id
        return Result.success(message="Reset")

    def list_simulators(self) -> Result[list[dict]]:
        return Result.success(data=[{"udid": "TEST"}], message="Listed")

    def take_screenshot(
        self, device_id: Optional[str], output_path: Optional[str]
    ) -> Result[dict]:
        self.last_device_id = device_id
        return Result.success(data={"path": output_path}, message="Screenshot")

    def handle_permission_alert(self, action: str) -> Result[None]:
        self.last_action = action
        return Result.success(message="Alert handled")

    def set_target_window_title(self, title_substring: Optional[str]) -> Result[dict]:
        self.last_window_title = title_substring
        return Result.success(data={"title_contains": title_substring}, message="Target set")

    def wait_for_element(self, identifier: str, timeout: float) -> Result[dict]:
        self.last_identifier = identifier
        self.last_timeout = timeout
        return Result.success(data={"identifier": identifier}, message="Found")

    def wait_for_element_gone(self, identifier: str, timeout: float) -> Result[None]:
        self.last_identifier = identifier
        self.last_timeout = timeout
        return Result.success(message="Gone")

    def wait_for_text(self, text: str, timeout: float) -> Result[dict]:
        self.last_text = text
        self.last_timeout = timeout
        return Result.success(data={"text": text}, message="Found text")

    def is_element_visible(self, identifier: str) -> Result[bool]:
        self.last_identifier = identifier
        return Result.success(data=True, message="Visible")

    def is_element_enabled(self, identifier: str) -> Result[bool]:
        self.last_identifier = identifier
        return Result.success(data=True, message="Enabled")

    def get_element_text(self, identifier: str) -> Result[str]:
        self.last_identifier = identifier
        return Result.success(data="Sample", message="Text")

    def get_element_attribute(self, identifier: str, attribute: str) -> Result:
        self.last_identifier = identifier
        self.last_attribute = attribute
        return Result.success(data="AXRole", message="Attribute")

    def get_element_count(self, identifier: str) -> Result[int]:
        self.last_identifier = identifier
        return Result.success(data=1, message="Count")

    def swipe(
        self,
        direction: str,
        start_x: Optional[float],
        start_y: Optional[float],
        distance: float,
        duration: float,
    ) -> Result[None]:
        self.last_direction = direction
        self.last_coordinates = (start_x, start_y)
        self.last_duration = duration
        return Result.success(message="Swiped")

    def scroll_to_element(
        self, identifier: str, max_scrolls: int, direction: str
    ) -> Result[dict]:
        self.last_identifier = identifier
        self.last_direction = direction
        return Result.success(data={"identifier": identifier}, message="Scrolled")

    def long_press(self, identifier: str, duration: float) -> Result[None]:
        self.last_identifier = identifier
        self.last_duration = duration
        return Result.success(message="Long press")

    def long_press_coordinates(
        self, x: float, y: float, duration: float
    ) -> Result[None]:
        self.last_coordinates = (x, y)
        self.last_duration = duration
        return Result.success(message="Long press coordinates")

    def assert_element_exists(self, identifier: str) -> Result[None]:
        self.last_identifier = identifier
        return Result.success(message="Exists")

    def assert_element_not_exists(self, identifier: str) -> Result[None]:
        self.last_identifier = identifier
        return Result.success(message="Not exists")

    def assert_element_visible(self, identifier: str) -> Result[None]:
        self.last_identifier = identifier
        return Result.success(message="Visible")

    def assert_element_enabled(self, identifier: str) -> Result[None]:
        self.last_identifier = identifier
        return Result.success(message="Enabled")

    def assert_text_equals(self, identifier: str, expected: str) -> Result[None]:
        self.last_identifier = identifier
        self.last_expected = expected
        return Result.success(message="Text equals")

    def assert_text_contains(self, identifier: str, substring: str) -> Result[None]:
        self.last_identifier = identifier
        self.last_substring = substring
        return Result.success(message="Text contains")

    def assert_element_count(self, identifier: str, expected_count: int) -> Result[None]:
        self.last_identifier = identifier
        self.last_expected_count = expected_count
        return Result.success(message="Count")

    def tap_element_with_retry(
        self, identifier: str, retries: int, interval: float
    ) -> Result[None]:
        self.last_identifier = identifier
        self.last_retries = retries
        self.last_interval = interval
        return Result.success(message="Tapped with retry")

    def input_text_with_retry(
        self, identifier: str, text: str, retries: int, interval: float
    ) -> Result[None]:
        self.last_identifier = identifier
        self.last_text = text
        self.last_retries = retries
        self.last_interval = interval
        return Result.success(message="Input with retry")


def test_list_ui_tree_usecase_returns_tree() -> None:
    repository = FakeSimulatorRepository()
    usecase = ListUiTreeUsecase(repository)

    tree = usecase.execute()

    assert tree.role == "AXWindow"


def test_tap_element_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = TapElementUsecase(repository)

    result = usecase.execute("Login")

    assert result.is_success is True
    assert repository.last_identifier == "Login"


def test_input_text_usecase_passes_text() -> None:
    repository = FakeSimulatorRepository()
    usecase = InputTextUsecase(repository)

    result = usecase.execute("Field", "Hello")

    assert result.is_success is True
    assert repository.last_identifier == "Field"
    assert repository.last_text == "Hello"


def test_launch_app_usecase_passes_bundle_id() -> None:
    repository = FakeSimulatorRepository()
    usecase = LaunchAppUsecase(repository)

    result = usecase.execute("com.example.app", None)

    assert result.is_success is True
    assert repository.last_bundle_id == "com.example.app"


def test_stop_app_usecase_passes_bundle_id() -> None:
    repository = FakeSimulatorRepository()
    usecase = StopAppUsecase(repository)

    result = usecase.execute("com.example.app", "DEVICE")

    assert result.is_success is True
    assert repository.last_bundle_id == "com.example.app"
    assert repository.last_device_id == "DEVICE"


def test_reset_app_usecase_passes_bundle_id() -> None:
    repository = FakeSimulatorRepository()
    usecase = ResetAppUsecase(repository)

    result = usecase.execute("com.example.app", "DEVICE")

    assert result.is_success is True
    assert repository.last_bundle_id == "com.example.app"
    assert repository.last_device_id == "DEVICE"


def test_list_simulators_usecase_returns_list() -> None:
    repository = FakeSimulatorRepository()
    usecase = ListSimulatorsUsecase(repository)

    result = usecase.execute()

    assert result.is_success is True
    assert result.data == [{"udid": "TEST"}]


def test_take_screenshot_usecase_passes_path() -> None:
    repository = FakeSimulatorRepository()
    usecase = TakeScreenshotUsecase(repository)

    result = usecase.execute("DEVICE", "/tmp/screen.png")

    assert result.is_success is True
    assert repository.last_device_id == "DEVICE"
    assert result.data == {"path": "/tmp/screen.png"}


def test_handle_permission_alert_usecase_passes_action() -> None:
    repository = FakeSimulatorRepository()
    usecase = HandlePermissionAlertUsecase(repository)

    result = usecase.execute("allow")

    assert result.is_success is True
    assert repository.last_action == "allow"


def test_set_target_window_usecase_passes_title() -> None:
    repository = FakeSimulatorRepository()
    usecase = SetTargetWindowUsecase(repository)

    result = usecase.execute("iPhone 15 Pro")

    assert result.is_success is True
    assert repository.last_window_title == "iPhone 15 Pro"


def test_tap_coordinates_usecase_passes_coordinates() -> None:
    repository = FakeSimulatorRepository()
    usecase = TapCoordinatesUsecase(repository)

    result = usecase.execute(10.0, 20.0)

    assert result.is_success is True
    assert repository.last_coordinates == (10.0, 20.0)


def test_wait_for_element_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = WaitForElementUsecase(repository)

    result = usecase.execute("Login", 5.0)

    assert result.is_success is True
    assert repository.last_identifier == "Login"
    assert repository.last_timeout == 5.0


def test_wait_for_element_gone_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = WaitForElementGoneUsecase(repository)

    result = usecase.execute("Spinner", 3.0)

    assert result.is_success is True
    assert repository.last_identifier == "Spinner"
    assert repository.last_timeout == 3.0


def test_wait_for_text_usecase_passes_text() -> None:
    repository = FakeSimulatorRepository()
    usecase = WaitForTextUsecase(repository)

    result = usecase.execute("Welcome", 4.0)

    assert result.is_success is True
    assert repository.last_text == "Welcome"
    assert repository.last_timeout == 4.0


def test_is_element_visible_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = IsElementVisibleUsecase(repository)

    result = usecase.execute("Login")

    assert result.is_success is True
    assert repository.last_identifier == "Login"


def test_is_element_enabled_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = IsElementEnabledUsecase(repository)

    result = usecase.execute("Login")

    assert result.is_success is True
    assert repository.last_identifier == "Login"


def test_get_element_text_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = GetElementTextUsecase(repository)

    result = usecase.execute("Login")

    assert result.is_success is True
    assert repository.last_identifier == "Login"
    assert result.data == "Sample"


def test_get_element_attribute_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = GetElementAttributeUsecase(repository)

    result = usecase.execute("Login", "AXRole")

    assert result.is_success is True
    assert repository.last_identifier == "Login"
    assert repository.last_attribute == "AXRole"


def test_get_element_count_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = GetElementCountUsecase(repository)

    result = usecase.execute("Login")

    assert result.is_success is True
    assert repository.last_identifier == "Login"
    assert result.data == 1


def test_swipe_usecase_passes_direction() -> None:
    repository = FakeSimulatorRepository()
    usecase = SwipeUsecase(repository)

    result = usecase.execute("up", None, None, 200.0, 0.2)

    assert result.is_success is True
    assert repository.last_direction == "up"
    assert repository.last_duration == 0.2


def test_scroll_to_element_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = ScrollToElementUsecase(repository)

    result = usecase.execute("Target", 5, "down")

    assert result.is_success is True
    assert repository.last_identifier == "Target"
    assert repository.last_direction == "down"


def test_long_press_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = LongPressUsecase(repository)

    result = usecase.execute("Login", 1.5)

    assert result.is_success is True
    assert repository.last_identifier == "Login"
    assert repository.last_duration == 1.5


def test_long_press_coordinates_usecase_passes_coordinates() -> None:
    repository = FakeSimulatorRepository()
    usecase = LongPressCoordinatesUsecase(repository)

    result = usecase.execute(12.0, 24.0, 1.2)

    assert result.is_success is True
    assert repository.last_coordinates == (12.0, 24.0)
    assert repository.last_duration == 1.2


def test_assertions_usecase_passes_identifier() -> None:
    repository = FakeSimulatorRepository()
    usecase = AssertionsUsecase(repository)

    assert usecase.assert_element_exists("Login").is_success is True
    assert repository.last_identifier == "Login"

    assert usecase.assert_element_not_exists("Missing").is_success is True
    assert repository.last_identifier == "Missing"

    assert usecase.assert_element_visible("Visible").is_success is True
    assert repository.last_identifier == "Visible"

    assert usecase.assert_element_enabled("Enabled").is_success is True
    assert repository.last_identifier == "Enabled"

    assert usecase.assert_text_equals("Label", "Hello").is_success is True
    assert repository.last_expected == "Hello"

    assert usecase.assert_text_contains("Label", "ell").is_success is True
    assert repository.last_substring == "ell"

    assert usecase.assert_element_count("Items", 2).is_success is True
    assert repository.last_expected_count == 2


def test_tap_with_retry_usecase_passes_args() -> None:
    repository = FakeSimulatorRepository()
    usecase = TapWithRetryUsecase(repository)

    result = usecase.execute("Login", 2, 0.1)

    assert result.is_success is True
    assert repository.last_identifier == "Login"
    assert repository.last_retries == 2
    assert repository.last_interval == 0.1


def test_input_text_with_retry_usecase_passes_args() -> None:
    repository = FakeSimulatorRepository()
    usecase = InputTextWithRetryUsecase(repository)

    result = usecase.execute("Field", "Hello", 2, 0.1)

    assert result.is_success is True
    assert repository.last_identifier == "Field"
    assert repository.last_text == "Hello"
    assert repository.last_retries == 2
    assert repository.last_interval == 0.1
