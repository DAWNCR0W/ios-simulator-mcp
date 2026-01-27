"""Entry point for the iOS Simulator MCP server."""

import argparse
import logging
import sys

from lib.core.logging.logger import configure_logger
from lib.features.simulator_control.data.datasources.accessibility_datasource import (
    AccessibilityDatasource,
)
from lib.features.simulator_control.data.datasources.simctl_datasource import SimctlDatasource
from lib.features.simulator_control.data.datasources.simulator_process_datasource import (
    SimulatorProcessDatasource,
)
from lib.features.simulator_control.data.repositories.simulator_repository_impl import (
    SimulatorRepositoryImpl,
)

# Core use cases
from lib.features.simulator_control.domain.usecases.input_text_usecase import (
    InputTextUsecase,
)
from lib.features.simulator_control.domain.usecases.install_app_usecase import (
    InstallAppUsecase,
)
from lib.features.simulator_control.domain.usecases.launch_app_usecase import (
    LaunchAppUsecase,
)
from lib.features.simulator_control.domain.usecases.list_simulators_usecase import (
    ListSimulatorsUsecase,
)
from lib.features.simulator_control.domain.usecases.list_runtimes_usecase import (
    ListRuntimesUsecase,
)
from lib.features.simulator_control.domain.usecases.list_device_types_usecase import (
    ListDeviceTypesUsecase,
)
from lib.features.simulator_control.domain.usecases.list_installed_apps_usecase import (
    ListInstalledAppsUsecase,
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
from lib.features.simulator_control.domain.usecases.tap_coordinates_usecase import (
    TapCoordinatesUsecase,
)
from lib.features.simulator_control.domain.usecases.take_screenshot_usecase import (
    TakeScreenshotUsecase,
)
from lib.features.simulator_control.domain.usecases.create_simulator_usecase import (
    CreateSimulatorUsecase,
)
from lib.features.simulator_control.domain.usecases.delete_simulator_usecase import (
    DeleteSimulatorUsecase,
)
from lib.features.simulator_control.domain.usecases.erase_simulator_usecase import (
    EraseSimulatorUsecase,
)
from lib.features.simulator_control.domain.usecases.get_app_container_usecase import (
    GetAppContainerUsecase,
)
from lib.features.simulator_control.domain.usecases.push_file_usecase import (
    PushFileUsecase,
)
from lib.features.simulator_control.domain.usecases.pull_file_usecase import (
    PullFileUsecase,
)
from lib.features.simulator_control.domain.usecases.set_privacy_usecase import (
    SetPrivacyUsecase,
)
from lib.features.simulator_control.domain.usecases.add_media_usecase import (
    AddMediaUsecase,
)
from lib.features.simulator_control.domain.usecases.start_recording_usecase import (
    StartRecordingUsecase,
)
from lib.features.simulator_control.domain.usecases.stop_recording_usecase import (
    StopRecordingUsecase,
)
from lib.features.simulator_control.domain.usecases.boot_simulator_usecase import (
    BootSimulatorUsecase,
)
from lib.features.simulator_control.domain.usecases.shutdown_simulator_usecase import (
    ShutdownSimulatorUsecase,
)
from lib.features.simulator_control.domain.usecases.uninstall_app_usecase import (
    UninstallAppUsecase,
)
from lib.features.simulator_control.domain.usecases.open_url_usecase import (
    OpenUrlUsecase,
)
from lib.features.simulator_control.domain.usecases.set_clipboard_usecase import (
    SetClipboardUsecase,
)
from lib.features.simulator_control.domain.usecases.get_clipboard_usecase import (
    GetClipboardUsecase,
)
from lib.features.simulator_control.domain.usecases.handle_permission_alert_usecase import (
    HandlePermissionAlertUsecase,
)
from lib.features.simulator_control.domain.usecases.set_target_window_usecase import (
    SetTargetWindowUsecase,
)

# Wait use cases
from lib.features.simulator_control.domain.usecases.wait_for_element_usecase import (
    WaitForElementUsecase,
)
from lib.features.simulator_control.domain.usecases.wait_for_element_gone_usecase import (
    WaitForElementGoneUsecase,
)
from lib.features.simulator_control.domain.usecases.wait_for_text_usecase import (
    WaitForTextUsecase,
)

# Element state use cases
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

# Gesture use cases
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

# Assertion use case
from lib.features.simulator_control.domain.usecases.assertions_usecase import (
    AssertionsUsecase,
)

# Retry use cases
from lib.features.simulator_control.domain.usecases.tap_with_retry_usecase import (
    TapWithRetryUsecase,
)
from lib.features.simulator_control.domain.usecases.input_text_with_retry_usecase import (
    InputTextWithRetryUsecase,
)

from lib.features.simulator_control.presentation.routes.mcp_routes import register_routes
from lib.features.simulator_control.presentation.viewmodels.simulator_mcp_viewmodel import (
    SimulatorMcpViewModel,
)


def build_viewmodel() -> SimulatorMcpViewModel:
    """Wire up datasources, repository, and use cases."""
    process_datasource = SimulatorProcessDatasource()
    accessibility_datasource = AccessibilityDatasource(process_datasource)
    simctl_datasource = SimctlDatasource()
    repository = SimulatorRepositoryImpl(accessibility_datasource, simctl_datasource)

    return SimulatorMcpViewModel(
        # Core use cases
        list_ui_tree_usecase=ListUiTreeUsecase(repository),
        tap_element_usecase=TapElementUsecase(repository),
        tap_coordinates_usecase=TapCoordinatesUsecase(repository),
        input_text_usecase=InputTextUsecase(repository),
        launch_app_usecase=LaunchAppUsecase(repository),
        stop_app_usecase=StopAppUsecase(repository),
        reset_app_usecase=ResetAppUsecase(repository),
        list_simulators_usecase=ListSimulatorsUsecase(repository),
        take_screenshot_usecase=TakeScreenshotUsecase(repository),
        list_runtimes_usecase=ListRuntimesUsecase(repository),
        list_device_types_usecase=ListDeviceTypesUsecase(repository),
        create_simulator_usecase=CreateSimulatorUsecase(repository),
        delete_simulator_usecase=DeleteSimulatorUsecase(repository),
        erase_simulator_usecase=EraseSimulatorUsecase(repository),
        list_installed_apps_usecase=ListInstalledAppsUsecase(repository),
        get_app_container_usecase=GetAppContainerUsecase(repository),
        push_file_usecase=PushFileUsecase(repository),
        pull_file_usecase=PullFileUsecase(repository),
        set_privacy_usecase=SetPrivacyUsecase(repository),
        add_media_usecase=AddMediaUsecase(repository),
        start_recording_usecase=StartRecordingUsecase(repository),
        stop_recording_usecase=StopRecordingUsecase(repository),
        boot_simulator_usecase=BootSimulatorUsecase(repository),
        shutdown_simulator_usecase=ShutdownSimulatorUsecase(repository),
        install_app_usecase=InstallAppUsecase(repository),
        uninstall_app_usecase=UninstallAppUsecase(repository),
        open_url_usecase=OpenUrlUsecase(repository),
        set_clipboard_usecase=SetClipboardUsecase(repository),
        get_clipboard_usecase=GetClipboardUsecase(repository),
        handle_permission_alert_usecase=HandlePermissionAlertUsecase(repository),
        set_target_window_usecase=SetTargetWindowUsecase(repository),
        # Wait use cases
        wait_for_element_usecase=WaitForElementUsecase(repository),
        wait_for_element_gone_usecase=WaitForElementGoneUsecase(repository),
        wait_for_text_usecase=WaitForTextUsecase(repository),
        # Element state use cases
        is_element_visible_usecase=IsElementVisibleUsecase(repository),
        is_element_enabled_usecase=IsElementEnabledUsecase(repository),
        get_element_text_usecase=GetElementTextUsecase(repository),
        get_element_attribute_usecase=GetElementAttributeUsecase(repository),
        get_element_count_usecase=GetElementCountUsecase(repository),
        # Gesture use cases
        swipe_usecase=SwipeUsecase(repository),
        scroll_to_element_usecase=ScrollToElementUsecase(repository),
        long_press_usecase=LongPressUsecase(repository),
        long_press_coordinates_usecase=LongPressCoordinatesUsecase(repository),
        # Assertion use case
        assertions_usecase=AssertionsUsecase(repository),
        # Retry use cases
        tap_with_retry_usecase=TapWithRetryUsecase(repository),
        input_text_with_retry_usecase=InputTextWithRetryUsecase(repository),
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="iOS Simulator MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode for MCP server",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP transport",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port for HTTP transport",
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="Path for HTTP transport",
    )
    return parser.parse_args()


def main() -> None:
    """Run the MCP server."""
    configure_logger()
    args = parse_args()
    logging.getLogger(__name__).info("Starting MCP server with %s transport", args.transport)

    try:
        from fastmcp import FastMCP
    except ImportError:
        from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("ios-simulator-mcp")
    viewmodel = build_viewmodel()
    register_routes(mcp, viewmodel)

    if args.transport == "http":
        try:
            mcp.run(transport="http", host=args.host, port=args.port, path=args.path)
        except TypeError:
            try:
                mcp.run(transport="streamable-http", host=args.host, port=args.port, path=args.path)
            except TypeError:
                mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        logging.getLogger(__name__).exception("Server failed: %s", error)
        sys.exit(1)
