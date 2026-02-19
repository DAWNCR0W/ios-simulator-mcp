"""Tests for simctl datasource resilience and caching behavior."""

import json
import subprocess

import pytest

from lib.core.errors.app_errors import SimctlError
from lib.features.simulator_control.data.datasources.simctl_datasource import SimctlDatasource


def test_run_simctl_retries_for_safe_read_commands(monkeypatch):
    datasource = SimctlDatasource()
    datasource._retry_count = 1

    calls = {"count": 0}

    def fake_run(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return subprocess.CompletedProcess(_args[0], 1, stdout="", stderr="temporary error")
        payload = {"devices": {"runtime": [{"udid": "A", "state": "Booted"}]}}
        return subprocess.CompletedProcess(_args[0], 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = datasource._run_simctl(["list", "devices", "booted", "-j"])

    assert calls["count"] == 2
    assert "Booted" in result


def test_run_simctl_does_not_retry_unsafe_commands(monkeypatch):
    datasource = SimctlDatasource()
    datasource._retry_count = 3

    calls = {"count": 0}

    def fake_run(*_args, **_kwargs):
        calls["count"] += 1
        return subprocess.CompletedProcess(_args[0], 1, stdout="", stderr="create failed")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(SimctlError):
        datasource._run_simctl(["create", "name", "device", "runtime"])

    assert calls["count"] == 1


def test_run_simctl_timeout_raises_actionable_error(monkeypatch):
    datasource = SimctlDatasource()
    datasource._retry_count = 0
    datasource._command_timeout_seconds = 0.01

    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=_args[0], timeout=0.01)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(SimctlError) as error:
        datasource._run_simctl(["list", "runtimes", "-j"])

    assert "timed out" in str(error.value)


def test_resolve_device_uses_booted_cache(monkeypatch):
    datasource = SimctlDatasource()
    datasource._default_device_id = None
    datasource._booted_cache_ttl_seconds = 10.0

    calls = {"count": 0}

    def fake_run_simctl(_args, _input_text=None, _retryable=None):
        calls["count"] += 1
        payload = {"devices": {"runtime": [{"udid": "BOOTED-1", "state": "Booted"}]}}
        return json.dumps(payload)

    monkeypatch.setattr(datasource, "_run_simctl", fake_run_simctl)

    first = datasource._resolve_device_id(None)
    second = datasource._resolve_device_id(None)

    assert first == "BOOTED-1"
    assert second == "BOOTED-1"
    assert calls["count"] == 1


def test_boot_simulator_is_idempotent_when_already_booted(monkeypatch):
    datasource = SimctlDatasource()
    monkeypatch.setattr(datasource, "_resolve_device_id_for_boot", lambda _device_id: "BOOTED-1")
    monkeypatch.setattr(
        datasource,
        "_run_simctl",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            SimctlError("Unable to boot device in current state: Booted")
        ),
    )

    result = datasource.boot_simulator(None)

    assert result.is_success is True
    assert result.data == {"device_id": "BOOTED-1"}


def test_list_installed_apps_parses_openstep_output_via_plutil(monkeypatch):
    datasource = SimctlDatasource()
    monkeypatch.setattr(datasource, "_resolve_device_id", lambda _device_id: "BOOTED-1")
    monkeypatch.setattr(
        datasource,
        "_run_simctl",
        lambda _args: '{ "com.example.app" = { CFBundleName = Example; }; }',
    )

    plutil_payload = {
        "com.example.app": {
            "CFBundleName": "Example",
            "Path": "/Applications/Example.app",
            "DataContainer": "file:///tmp/example-data/",
            "GroupContainers": {"group.example": "file:///tmp/example-group/"},
        }
    }
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            _args[0], 0, stdout=json.dumps(plutil_payload), stderr=""
        ),
    )

    result = datasource.list_installed_apps(None)

    assert result.is_success is True
    assert len(result.data) == 1
    app = result.data[0]
    assert app["bundle_id"] == "com.example.app"
    assert app["bundle_name"] == "Example"
    assert app["bundle_path"] == "/Applications/Example.app"
    assert app["data_container"] == "/tmp/example-data"
    assert app["group_containers"] == {"group.example": "/tmp/example-group"}


def test_list_installed_apps_returns_failure_when_plutil_conversion_fails(monkeypatch):
    datasource = SimctlDatasource()
    monkeypatch.setattr(datasource, "_resolve_device_id", lambda _device_id: "BOOTED-1")
    monkeypatch.setattr(datasource, "_run_simctl", lambda _args: "not-json-not-plist")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            _args[0], 1, stdout="", stderr="conversion failed"
        ),
    )

    result = datasource.list_installed_apps(None)

    assert result.is_success is False
    assert "Failed to parse simctl listapps output" in result.message


def test_push_file_copies_file_into_simulator_data_path(tmp_path, monkeypatch):
    datasource = SimctlDatasource()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(datasource, "_resolve_device_id", lambda _device_id: "DEVICE-1")

    device_root = tmp_path / "Library/Developer/CoreSimulator/Devices/DEVICE-1/data"
    device_root.mkdir(parents=True, exist_ok=True)

    source = tmp_path / "source.txt"
    source.write_text("roundtrip", encoding="utf-8")

    result = datasource.push_file(str(source), "/tmp/copied.txt", None)

    assert result.is_success is True
    copied = device_root / "tmp/copied.txt"
    assert copied.exists()
    assert copied.read_text(encoding="utf-8") == "roundtrip"


def test_pull_file_copies_file_from_simulator_data_path(tmp_path, monkeypatch):
    datasource = SimctlDatasource()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(datasource, "_resolve_device_id", lambda _device_id: "DEVICE-1")

    device_root = tmp_path / "Library/Developer/CoreSimulator/Devices/DEVICE-1/data"
    source = device_root / "tmp/from-sim.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("from-simulator", encoding="utf-8")

    destination = tmp_path / "out/pulled.txt"
    result = datasource.pull_file("/tmp/from-sim.txt", str(destination), None)

    assert result.is_success is True
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == "from-simulator"


def test_push_file_rejects_relative_simulator_destination_path(tmp_path, monkeypatch):
    datasource = SimctlDatasource()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(datasource, "_resolve_device_id", lambda _device_id: "DEVICE-1")

    device_root = tmp_path / "Library/Developer/CoreSimulator/Devices/DEVICE-1/data"
    device_root.mkdir(parents=True, exist_ok=True)

    source = tmp_path / "source.txt"
    source.write_text("value", encoding="utf-8")

    result = datasource.push_file(str(source), "tmp/relative.txt", None)

    assert result.is_success is False
    assert "Simulator path must be absolute" in result.message


def test_pull_file_returns_failure_when_source_is_missing(tmp_path, monkeypatch):
    datasource = SimctlDatasource()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(datasource, "_resolve_device_id", lambda _device_id: "DEVICE-1")

    device_root = tmp_path / "Library/Developer/CoreSimulator/Devices/DEVICE-1/data"
    device_root.mkdir(parents=True, exist_ok=True)

    destination = tmp_path / "out/pulled.txt"
    result = datasource.pull_file("/tmp/missing.txt", str(destination), None)

    assert result.is_success is False
    assert "Source path not found on simulator" in result.message


def test_reset_app_ignores_terminate_when_app_not_running(monkeypatch):
    datasource = SimctlDatasource()
    monkeypatch.setattr(datasource, "_resolve_device_id", lambda _device_id: "DEVICE-1")

    calls = []

    def fake_run_simctl(args, *_unused):
        calls.append(args)
        if args[0] == "terminate":
            raise SimctlError("found nothing to terminate")
        return ""

    monkeypatch.setattr(datasource, "_run_simctl", fake_run_simctl)

    result = datasource.reset_app("com.example.app", None)

    assert result.is_success is True
    assert calls[0][0] == "terminate"
    assert calls[1][0] == "uninstall"


def test_reset_app_returns_failure_for_unexpected_terminate_error(monkeypatch):
    datasource = SimctlDatasource()
    monkeypatch.setattr(datasource, "_resolve_device_id", lambda _device_id: "DEVICE-1")
    monkeypatch.setattr(
        datasource,
        "_run_simctl",
        lambda args, *_unused: (_ for _ in ()).throw(SimctlError("permission denied"))
        if args[0] == "terminate"
        else "",
    )

    result = datasource.reset_app("com.example.app", None)

    assert result.is_success is False
    assert "permission denied" in result.message
