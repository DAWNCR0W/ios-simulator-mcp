"""Datasource for interacting with simctl CLI."""

import json
import os
import signal
import subprocess
import time
from datetime import datetime
from typing import Optional

from lib.core.constants.app_constants import (
    DEFAULT_BOOTED_DEVICE_CACHE_TTL_SECONDS,
    DEFAULT_DEVICE_ID_ENV,
    DEFAULT_SIMCTL_RETRY_BACKOFF_SECONDS,
    DEFAULT_SIMCTL_RETRY_COUNT,
    DEFAULT_SIMCTL_TIMEOUT_SECONDS,
)
from lib.core.errors.app_errors import SimctlError
from lib.core.utils.result import Result


class SimctlDatasource:
    """Runs simctl commands for simulator management."""

    def __init__(self) -> None:
        self._default_device_id = os.getenv(DEFAULT_DEVICE_ID_ENV)
        self._recording_processes: dict[str, dict[str, object]] = {}
        self._command_timeout_seconds = float(
            os.getenv("IOS_SIM_SIMCTL_TIMEOUT_SECONDS", str(DEFAULT_SIMCTL_TIMEOUT_SECONDS))
        )
        self._retry_count = max(
            0,
            int(os.getenv("IOS_SIM_SIMCTL_RETRY_COUNT", str(DEFAULT_SIMCTL_RETRY_COUNT))),
        )
        self._retry_backoff_seconds = max(
            0.0,
            float(
                os.getenv(
                    "IOS_SIM_SIMCTL_RETRY_BACKOFF_SECONDS",
                    str(DEFAULT_SIMCTL_RETRY_BACKOFF_SECONDS),
                )
            ),
        )
        self._booted_cache_ttl_seconds = max(
            0.0,
            float(
                os.getenv(
                    "IOS_SIM_BOOTED_CACHE_TTL_SECONDS",
                    str(DEFAULT_BOOTED_DEVICE_CACHE_TTL_SECONDS),
                )
            ),
        )
        self._booted_cache_timestamp = 0.0
        self._booted_cache: list[str] = []

    def list_simulators(self) -> Result[list[dict]]:
        """Return a list of available simulator devices."""
        try:
            flattened = self._get_all_devices()
            return Result.success(data=flattened, message="Simulators listed")
        except (json.JSONDecodeError, SimctlError) as error:
            return Result.failure(str(error))

    def list_runtimes(self) -> Result[list[dict]]:
        """Return a list of available simulator runtimes."""
        try:
            output = self._run_simctl(["list", "runtimes", "-j"]).strip()
            payload = json.loads(output)
            runtimes = payload.get("runtimes", [])
            mapped = []
            for runtime in runtimes:
                mapped.append(
                    {
                        "identifier": runtime.get("identifier"),
                        "name": runtime.get("name"),
                        "version": runtime.get("version"),
                        "is_available": runtime.get("isAvailable", False),
                        "availability_error": runtime.get("availabilityError"),
                    }
                )
            return Result.success(data=mapped, message="Runtimes listed")
        except (json.JSONDecodeError, SimctlError) as error:
            return Result.failure(str(error))

    def list_device_types(self) -> Result[list[dict]]:
        """Return a list of available simulator device types."""
        try:
            output = self._run_simctl(["list", "devicetypes", "-j"]).strip()
            payload = json.loads(output)
            types = payload.get("devicetypes", [])
            mapped = []
            for item in types:
                mapped.append(
                    {
                        "name": item.get("name"),
                        "identifier": item.get("identifier"),
                    }
                )
            return Result.success(data=mapped, message="Device types listed")
        except (json.JSONDecodeError, SimctlError) as error:
            return Result.failure(str(error))

    def create_simulator(
        self, name: str, device_type_id: str, runtime_id: str
    ) -> Result[dict]:
        """Create a new simulator device."""
        if not name.strip():
            return Result.failure("Simulator name must not be empty.")
        if not device_type_id.strip():
            return Result.failure("Device type identifier must not be empty.")
        if not runtime_id.strip():
            return Result.failure("Runtime identifier must not be empty.")

        udid = self._run_simctl(
            ["create", name.strip(), device_type_id.strip(), runtime_id.strip()]
        ).strip()
        self._invalidate_booted_cache()
        return Result.success(data={"udid": udid}, message="Simulator created")

    def delete_simulator(self, device_id: str) -> Result[None]:
        """Delete a simulator device by UDID."""
        if not device_id.strip():
            return Result.failure("Device ID must not be empty.")
        self._run_simctl(["delete", device_id.strip()])
        self._invalidate_booted_cache()
        return Result.success(message="Simulator deleted")

    def erase_simulator(self, device_id: Optional[str], all_devices: bool) -> Result[dict]:
        """Erase simulator data for a device or all devices."""
        if all_devices:
            self._run_simctl(["erase", "all"])
            self._invalidate_booted_cache()
            return Result.success(data={"target": "all"}, message="Simulators erased")

        if not device_id or not device_id.strip():
            return Result.failure("Device ID required unless all_devices is true.")
        self._run_simctl(["erase", device_id.strip()])
        self._invalidate_booted_cache()
        return Result.success(data={"target": device_id.strip()}, message="Simulator erased")

    def list_installed_apps(self, device_id: Optional[str]) -> Result[list[dict]]:
        """Return a list of installed apps on the simulator."""
        try:
            resolved_device = self._resolve_device_id(device_id)
            output = self._run_simctl(["listapps", resolved_device, "-j"]).strip()
            payload = json.loads(output)
            apps = payload.get("apps", {})
            flattened = []
            for bundle_id, info in apps.items():
                flattened.append(
                    {
                        "bundle_id": bundle_id,
                        "bundle_name": info.get("bundleName"),
                        "bundle_path": info.get("bundlePath"),
                        "app_container": info.get("appContainer"),
                        "data_container": info.get("dataContainer"),
                        "group_containers": info.get("groupContainers"),
                    }
                )
            return Result.success(data=flattened, message="Apps listed")
        except (json.JSONDecodeError, SimctlError) as error:
            return Result.failure(str(error))

    def get_app_container(
        self, bundle_id: str, device_id: Optional[str], container_type: Optional[str]
    ) -> Result[dict]:
        """Return the app container path for a bundle."""
        if not bundle_id.strip():
            return Result.failure("Bundle ID must not be empty.")
        resolved_device = self._resolve_device_id(device_id)
        args = ["get_app_container", resolved_device, bundle_id.strip()]
        if container_type:
            args.append(container_type.strip())
        path = self._run_simctl(args).strip()
        return Result.success(
            data={"path": path, "bundle_id": bundle_id.strip(), "container_type": container_type},
            message="App container resolved",
        )

    def push_file(
        self, source_path: str, destination_path: str, device_id: Optional[str]
    ) -> Result[None]:
        """Push a file to the simulator."""
        if not source_path.strip():
            return Result.failure("Source path must not be empty.")
        if not destination_path.strip():
            return Result.failure("Destination path must not be empty.")
        resolved_device = self._resolve_device_id(device_id)
        resolved_source = os.path.expanduser(source_path)
        if not os.path.exists(resolved_source):
            return Result.failure(f"Source path not found: {resolved_source}")
        self._run_simctl(["push", resolved_device, resolved_source, destination_path.strip()])
        return Result.success(message="File pushed")

    def pull_file(
        self, source_path: str, destination_path: str, device_id: Optional[str]
    ) -> Result[None]:
        """Pull a file from the simulator."""
        if not source_path.strip():
            return Result.failure("Source path must not be empty.")
        if not destination_path.strip():
            return Result.failure("Destination path must not be empty.")
        resolved_device = self._resolve_device_id(device_id)
        resolved_destination = os.path.expanduser(destination_path)
        destination_dir = os.path.dirname(resolved_destination)
        if destination_dir:
            os.makedirs(destination_dir, exist_ok=True)
        self._run_simctl(["pull", resolved_device, source_path.strip(), resolved_destination])
        return Result.success(message="File pulled")

    def set_privacy(
        self,
        action: str,
        service: str,
        bundle_id: Optional[str],
        device_id: Optional[str],
    ) -> Result[None]:
        """Grant/revoke/reset privacy permissions for a service."""
        action_lower = action.strip().lower()
        if action_lower not in {"grant", "revoke", "reset"}:
            return Result.failure("Action must be grant, revoke, or reset.")
        if not service.strip():
            return Result.failure("Service must not be empty.")
        resolved_device = self._resolve_device_id(device_id)
        args = ["privacy", resolved_device, action_lower, service.strip()]
        if bundle_id:
            args.append(bundle_id.strip())
        self._run_simctl(args)
        return Result.success(message="Privacy updated")

    def add_media(self, media_paths: list[str], device_id: Optional[str]) -> Result[dict]:
        """Add media files to the simulator photo library."""
        if not media_paths:
            return Result.failure("Media paths must not be empty.")
        resolved_device = self._resolve_device_id(device_id)
        resolved_paths = []
        for path in media_paths:
            if not path.strip():
                return Result.failure("Media path must not be empty.")
            resolved = os.path.expanduser(path)
            if not os.path.exists(resolved):
                return Result.failure(f"Media path not found: {resolved}")
            resolved_paths.append(resolved)
        self._run_simctl(["addmedia", resolved_device, *resolved_paths])
        return Result.success(
            data={"count": len(resolved_paths), "device_id": resolved_device},
            message="Media added",
        )

    def start_recording(
        self, device_id: Optional[str], output_path: Optional[str]
    ) -> Result[dict]:
        """Start a simulator screen recording."""
        resolved_device = self._resolve_device_id(device_id)
        if resolved_device in self._recording_processes:
            return Result.failure("Recording already in progress for device.")

        target_path = self._resolve_video_output_path(output_path)
        command = ["xcrun", "simctl", "io", resolved_device, "recordVideo", target_path]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._recording_processes[resolved_device] = {
            "process": process,
            "path": target_path,
        }
        return Result.success(
            data={"path": target_path, "device_id": resolved_device},
            message="Recording started",
        )

    def stop_recording(self, device_id: Optional[str]) -> Result[dict]:
        """Stop a simulator screen recording."""
        resolved_device = self._resolve_device_id(device_id)
        entry = self._recording_processes.get(resolved_device)
        if not entry:
            return Result.failure("No active recording for device.")

        process = entry["process"]
        path = entry["path"]
        if process.poll() is not None:
            self._recording_processes.pop(resolved_device, None)
            return Result.failure("Recording process already stopped.")

        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
        self._recording_processes.pop(resolved_device, None)
        return Result.success(
            data={"path": path, "device_id": resolved_device},
            message="Recording stopped",
        )

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
        try:
            self._run_simctl(["io", resolved_device, "screenshot", target_path])
        except SimctlError:
            # Xcode 26 can require explicit image type for file output.
            self._run_simctl(["io", resolved_device, "screenshot", "--type=png", target_path])
        return Result.success(
            data={"path": target_path, "device_id": resolved_device},
            message="Screenshot saved",
        )

    def boot_simulator(self, device_id: Optional[str]) -> Result[dict]:
        """Boot a simulator device."""
        resolved_device = self._resolve_device_id_for_boot(device_id)
        try:
            self._run_simctl(["boot", resolved_device])
        except SimctlError as error:
            message = str(error)
            if "Unable to boot device in current state: Booted" not in message:
                raise
        self._invalidate_booted_cache()
        return Result.success(
            data={"device_id": resolved_device},
            message="Simulator booted",
        )

    def shutdown_simulator(self, device_id: Optional[str]) -> Result[dict]:
        """Shutdown a simulator device or all booted devices."""
        target = device_id or "booted"
        self._run_simctl(["shutdown", target])
        self._invalidate_booted_cache()
        return Result.success(
            data={"target": target},
            message="Simulator shutdown",
        )

    def install_app(self, app_path: str, device_id: Optional[str]) -> Result[None]:
        """Install an app bundle on the simulator."""
        resolved_device = self._resolve_device_id(device_id)
        resolved_path = os.path.expanduser(app_path)
        if not os.path.exists(resolved_path):
            return Result.failure(f"App path not found: {resolved_path}")
        self._run_simctl(["install", resolved_device, resolved_path])
        return Result.success(message="App installed")

    def uninstall_app(self, bundle_id: str, device_id: Optional[str]) -> Result[None]:
        """Uninstall an app bundle from the simulator."""
        resolved_device = self._resolve_device_id(device_id)
        self._run_simctl(["uninstall", resolved_device, bundle_id])
        return Result.success(message="App uninstalled")

    def open_url(self, url: str, device_id: Optional[str]) -> Result[None]:
        """Open a URL inside the simulator."""
        if not url:
            return Result.failure("URL must not be empty.")
        resolved_device = self._resolve_device_id(device_id)
        self._run_simctl(["openurl", resolved_device, url])
        return Result.success(message="URL opened")

    def set_clipboard(self, text: str, device_id: Optional[str]) -> Result[None]:
        """Set clipboard text on the simulator."""
        if text is None:
            return Result.failure("Clipboard text must not be None.")
        resolved_device = self._resolve_device_id(device_id)
        self._run_simctl(["pbcopy", resolved_device], input_text=text)
        return Result.success(message="Clipboard updated")

    def get_clipboard(self, device_id: Optional[str]) -> Result[str]:
        """Get clipboard text from the simulator."""
        resolved_device = self._resolve_device_id(device_id)
        output = self._run_simctl(["pbpaste", resolved_device])
        return Result.success(data=output.rstrip("\n"), message="Clipboard fetched")

    def _resolve_device_id(self, device_id: Optional[str]) -> str:
        if device_id:
            return device_id
        if self._default_device_id:
            return self._default_device_id
        booted_devices = self._get_booted_devices()
        if not booted_devices:
            raise SimctlError("No booted simulator devices found.")
        return booted_devices[0]

    def _resolve_device_id_for_boot(self, device_id: Optional[str]) -> str:
        if device_id:
            return device_id
        if self._default_device_id:
            return self._default_device_id

        devices = self._get_all_devices()
        for item in devices:
            if item.get("state") == "Booted":
                return item.get("udid")
        for item in devices:
            if item.get("is_available"):
                return item.get("udid")
        if devices:
            return devices[0].get("udid")
        raise SimctlError("No simulator devices available to boot.")

    def _get_all_devices(self) -> list[dict]:
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
        return flattened

    def _get_booted_devices(self) -> list[str]:
        now = time.monotonic()
        if (
            self._booted_cache_ttl_seconds > 0
            and self._booted_cache
            and (now - self._booted_cache_timestamp) < self._booted_cache_ttl_seconds
        ):
            return list(self._booted_cache)

        output = self._run_simctl(["list", "devices", "booted", "-j"]).strip()
        payload = json.loads(output)
        devices = payload.get("devices", {})
        booted = []
        for items in devices.values():
            for item in items:
                if item.get("state") == "Booted":
                    booted.append(item.get("udid"))
        self._booted_cache = list(booted)
        self._booted_cache_timestamp = now
        return booted

    def _invalidate_booted_cache(self) -> None:
        self._booted_cache_timestamp = 0.0
        self._booted_cache = []

    def _is_retry_safe(self, args: list[str]) -> bool:
        if not args:
            return False
        return args[0] in {
            "list",
            "listapps",
            "get_app_container",
            "pbpaste",
        }

    def _run_simctl(
        self,
        args: list[str],
        input_text: Optional[str] = None,
        retryable: Optional[bool] = None,
    ) -> str:
        command = ["xcrun", "simctl", *args]
        allow_retry = self._is_retry_safe(args) if retryable is None else retryable
        attempts = self._retry_count + 1 if allow_retry else 1
        last_error = "simctl command failed"
        last_stdout = ""

        for attempt in range(attempts):
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    input=input_text,
                    timeout=self._command_timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                last_error = (
                    f"simctl command timed out after {self._command_timeout_seconds:.1f}s: "
                    f"{' '.join(command)}"
                )
                if attempt == attempts - 1:
                    raise SimctlError(last_error) from error
                time.sleep(self._retry_backoff_seconds * (attempt + 1))
                continue

            last_stdout = result.stdout
            if result.returncode == 0:
                return result.stdout

            stderr = (result.stderr or "").strip()
            last_error = stderr or "simctl command failed"
            if attempt == attempts - 1:
                break
            time.sleep(self._retry_backoff_seconds * (attempt + 1))

        error_message = f"{last_error} (command: {' '.join(command)})"
        if last_stdout.strip():
            error_message = f"{error_message}; stdout: {last_stdout.strip()}"
        raise SimctlError(error_message)

    def _resolve_output_path(self, output_path: Optional[str]) -> str:
        if output_path:
            return os.path.expanduser(output_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"simulator_screenshot_{timestamp}.png"
        downloads_dir = os.path.expanduser("~/Downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        return os.path.join(downloads_dir, file_name)

    def _resolve_video_output_path(self, output_path: Optional[str]) -> str:
        if output_path:
            return os.path.expanduser(output_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"simulator_recording_{timestamp}.mp4"
        downloads_dir = os.path.expanduser("~/Downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        return os.path.join(downloads_dir, file_name)
