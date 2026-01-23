"""Datasource for interacting with simctl CLI."""

import json
import os
import subprocess
from datetime import datetime
from typing import Optional

from lib.core.constants.app_constants import DEFAULT_DEVICE_ID_ENV
from lib.core.errors.app_errors import SimctlError
from lib.core.utils.result import Result


class SimctlDatasource:
    """Runs simctl commands for simulator management."""

    def __init__(self) -> None:
        self._default_device_id = os.getenv(DEFAULT_DEVICE_ID_ENV)

    def list_simulators(self) -> Result[list[dict]]:
        """Return a list of available simulator devices."""
        try:
            output = self._run_simctl(["list", "devices", "-j"]).strip()
            payload = json.loads(output)
            devices = payload.get("devices", {})
            flattened = []
            for runtime, items in devices.items():
                for item in items:
                    flattened.append(
                        {
                            "runtime": runtime,
                            "name": item.get("name"),
                            "udid": item.get("udid"),
                            "state": item.get("state"),
                            "is_available": item.get("isAvailable", False),
                        }
                    )
            return Result.success(data=flattened, message="Simulators listed")
        except (json.JSONDecodeError, SimctlError) as error:
            return Result.failure(str(error))

    def launch_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Launch an app on the specified simulator device."""
        resolved_device = self._resolve_device_id(device_id)
        self._run_simctl(["launch", resolved_device, bundle_id])
        return Result.success(message="App launched")

    def stop_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Terminate an app on the specified simulator device."""
        resolved_device = self._resolve_device_id(device_id)
        self._run_simctl(["terminate", resolved_device, bundle_id])
        return Result.success(message="App terminated")

    def reset_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Terminate and uninstall an app from the simulator."""
        resolved_device = self._resolve_device_id(device_id)
        self._run_simctl(["terminate", resolved_device, bundle_id])
        self._run_simctl(["uninstall", resolved_device, bundle_id])
        return Result.success(message="App reset (uninstalled)")

    def take_screenshot(
        self, device_id: Optional[str], output_path: Optional[str]
    ) -> Result[dict]:
        """Capture a screenshot and save it to disk."""
        resolved_device = self._resolve_device_id(device_id)
        target_path = self._resolve_output_path(output_path)
        self._run_simctl(["io", resolved_device, "screenshot", target_path])
        return Result.success(
            data={"path": target_path, "device_id": resolved_device},
            message="Screenshot saved",
        )

    def _resolve_device_id(self, device_id: Optional[str]) -> str:
        if device_id:
            return device_id
        if self._default_device_id:
            return self._default_device_id
        booted_devices = self._get_booted_devices()
        if not booted_devices:
            raise SimctlError("No booted simulator devices found.")
        return booted_devices[0]

    def _get_booted_devices(self) -> list[str]:
        output = self._run_simctl(["list", "devices", "booted", "-j"]).strip()
        payload = json.loads(output)
        devices = payload.get("devices", {})
        booted = []
        for items in devices.values():
            for item in items:
                if item.get("state") == "Booted":
                    booted.append(item.get("udid"))
        return booted

    def _run_simctl(self, args: list[str]) -> str:
        command = ["xcrun", "simctl", *args]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise SimctlError(result.stderr.strip() or "simctl command failed")
        return result.stdout

    def _resolve_output_path(self, output_path: Optional[str]) -> str:
        if output_path:
            return os.path.expanduser(output_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"simulator_screenshot_{timestamp}.png"
        downloads_dir = os.path.expanduser("~/Downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        return os.path.join(downloads_dir, file_name)
