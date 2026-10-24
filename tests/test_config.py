"""Community Cloud reads secrets without committing credentials."""

import streamlit as st
import config


def test_api_key_uses_cloud_secrets(monkeypatch):
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.setattr(st, "secrets", {"RAPIDAPI_KEY": "test-cloud-key"})
    assert config.api_key() == "test-cloud-key"


def test_environment_key_has_precedence(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test-environment-key")
    monkeypatch.setattr(st, "secrets", {"RAPIDAPI_KEY": "test-cloud-key"})
    assert config.api_key() == "test-environment-key"


def test_hosting_flag_from_cloud_secrets(monkeypatch):
    monkeypatch.delenv("DEPLOYMENT_ENV", raising=False)
    monkeypatch.setattr(st, "secrets", {"DEPLOYMENT_ENV": "community-cloud"})
    assert config.cloud_deployment()
    monkeypatch.setenv("DEPLOYMENT_ENV", "local")
    assert not config.cloud_deployment()
