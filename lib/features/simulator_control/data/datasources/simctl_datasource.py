"""Datasource for interacting with simctl CLI."""

import json
import os
import shutil
import signal
import subprocess
import time
from datetime import datetime
from typing import Optional
from urllib.parse import unquote, urlparse

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
            output = self._run_simctl(["listapps", resolved_device]).strip()
            apps = self._extract_listapps_apps(output)
            flattened = []
            for bundle_id, info in apps.items():
                group_containers = self._normalize_group_containers(
                    info.get("groupContainers") or info.get("GroupContainers")
                )
                flattened.append(
                    {
                        "bundle_id": bundle_id,
                        "bundle_name": (
                            info.get("bundleName")
                            or info.get("CFBundleName")
                            or info.get("CFBundleDisplayName")
                        ),
                        "bundle_path": self._normalize_file_url(
                            info.get("bundlePath") or info.get("Path") or info.get("Bundle")
                        ),
                        "app_container": self._normalize_file_url(
                            info.get("appContainer") or info.get("AppContainer")
                        ),
                        "data_container": self._normalize_file_url(
                            info.get("dataContainer") or info.get("DataContainer")
                        ),
                        "group_containers": group_containers,
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
        try:
            resolved_device = self._resolve_device_id(device_id)
            resolved_source = os.path.expanduser(source_path)
            if not os.path.exists(resolved_source):
                return Result.failure(f"Source path not found: {resolved_source}")
            resolved_destination = self._resolve_simulator_data_path(
                resolved_device, destination_path.strip()
            )
            destination_dir = os.path.dirname(resolved_destination)
            if destination_dir:
                os.makedirs(destination_dir, exist_ok=True)

            if os.path.isdir(resolved_source):
                if os.path.exists(resolved_destination):
                    if os.path.isdir(resolved_destination):
                        shutil.rmtree(resolved_destination)
                    else:
                        os.remove(resolved_destination)
                shutil.copytree(resolved_source, resolved_destination)
            else:
                shutil.copy2(resolved_source, resolved_destination)
            return Result.success(message="File pushed")
        except (OSError, SimctlError) as error:
            return Result.failure(str(error))

    def pull_file(
        self, source_path: str, destination_path: str, device_id: Optional[str]
    ) -> Result[None]:
        """Pull a file from the simulator."""
        if not source_path.strip():
            return Result.failure("Source path must not be empty.")
        if not destination_path.strip():
            return Result.failure("Destination path must not be empty.")
        try:
            resolved_device = self._resolve_device_id(device_id)
            resolved_source = self._resolve_simulator_data_path(resolved_device, source_path.strip())
            if not os.path.exists(resolved_source):
                return Result.failure(f"Source path not found on simulator: {source_path.strip()}")
            resolved_destination = os.path.expanduser(destination_path)

            if os.path.isdir(resolved_source):
                if os.path.exists(resolved_destination):
                    if os.path.isdir(resolved_destination):
                        shutil.rmtree(resolved_destination)
                    else:
                        os.remove(resolved_destination)
                shutil.copytree(resolved_source, resolved_destination)
            else:
                destination_dir = os.path.dirname(resolved_destination)
                if destination_dir:
                    os.makedirs(destination_dir, exist_ok=True)
                shutil.copy2(resolved_source, resolved_destination)
            return Result.success(message="File pulled")
        except (OSError, SimctlError) as error:
            return Result.failure(str(error))

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
        try:
            self._run_simctl(["terminate", resolved_device, bundle_id])
        except SimctlError as error:
            message = str(error).lower()
            if "found nothing to terminate" not in message:
                return Result.failure(str(error))
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

    def _extract_listapps_apps(self, raw_output: str) -> dict[str, dict]:
        payload = self._parse_listapps_payload(raw_output)
        if "apps" in payload and isinstance(payload.get("apps"), dict):
            return payload["apps"]
        if all(isinstance(value, dict) for value in payload.values()):
            return payload
        raise SimctlError("Unexpected simctl listapps output format.")

    def _parse_listapps_payload(self, raw_output: str) -> dict:
        if not raw_output:
            return {}
        try:
            parsed = json.loads(raw_output)
            if isinstance(parsed, dict):
                return parsed
            raise SimctlError("Unexpected simctl listapps output format.")
        except json.JSONDecodeError:
            return self._convert_openstep_plist_to_json(raw_output)

    def _convert_openstep_plist_to_json(self, raw_output: str) -> dict:
        command = ["plutil", "-convert", "json", "-o", "-", "-"]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                input=raw_output,
                timeout=self._command_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise SimctlError("Timed out while parsing simctl listapps output.") from error

        if result.returncode != 0:
            stderr = (result.stderr or "").strip() or "plutil conversion failed"
            raise SimctlError(f"Failed to parse simctl listapps output: {stderr}")
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise SimctlError("Failed to parse simctl listapps JSON payload.") from error
        if not isinstance(parsed, dict):
            raise SimctlError("Unexpected simctl listapps payload type.")
        return parsed

    def _normalize_file_url(self, path_value: Optional[str]) -> Optional[str]:
        if not isinstance(path_value, str):
            return path_value
        if not path_value.startswith("file://"):
            return path_value
        parsed = urlparse(path_value)
        normalized = unquote(parsed.path)
        if normalized != "/" and normalized.endswith("/"):
            return normalized[:-1]
        return normalized

    def _normalize_group_containers(
        self, group_containers: Optional[dict]
    ) -> Optional[dict[str, str]]:
        if not isinstance(group_containers, dict):
            return None
        normalized: dict[str, str] = {}
        for key, value in group_containers.items():
            if not isinstance(key, str):
                continue
            normalized[key] = self._normalize_file_url(value) if isinstance(value, str) else value
        return normalized

    def _resolve_simulator_data_path(self, device_id: str, simulator_path: str) -> str:
        normalized_path = os.path.normpath(simulator_path.strip())
        if not normalized_path.startswith("/"):
            raise SimctlError("Simulator path must be absolute (for example: /tmp/file.txt).")
        if normalized_path == "/":
            raise SimctlError("Simulator path must not be root (/).")

        simulator_data_root = os.path.normpath(
            os.path.expanduser(f"~/Library/Developer/CoreSimulator/Devices/{device_id}/data")
        )
        if not os.path.isdir(simulator_data_root):
            raise SimctlError(f"Simulator data path not found for device: {device_id}")

        host_path = os.path.normpath(
            os.path.join(simulator_data_root, normalized_path.lstrip("/"))
        )
        if os.path.commonpath([simulator_data_root, host_path]) != simulator_data_root:
            raise SimctlError("Simulator path escapes the simulator data directory.")
        return host_path

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
