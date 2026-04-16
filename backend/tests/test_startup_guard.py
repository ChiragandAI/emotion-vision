import importlib
import sys

import pytest


def _reload_config(monkeypatch, env: dict[str, str]):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("app.core.config", None)
    return importlib.import_module("app.core.config")


def test_production_refuses_mock(monkeypatch):
    with pytest.raises(RuntimeError, match="mock"):
        _reload_config(monkeypatch, {"ENVIRONMENT": "production", "INFERENCE_MODE": "mock"})


def test_production_allows_local(monkeypatch):
    mod = _reload_config(monkeypatch, {"ENVIRONMENT": "production", "INFERENCE_MODE": "local"})
    assert mod.settings.inference_mode == "local"


def test_dev_allows_mock(monkeypatch):
    mod = _reload_config(monkeypatch, {"ENVIRONMENT": "dev", "INFERENCE_MODE": "mock"})
    assert mod.settings.inference_mode == "mock"
