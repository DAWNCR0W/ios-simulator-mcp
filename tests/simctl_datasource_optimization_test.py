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
