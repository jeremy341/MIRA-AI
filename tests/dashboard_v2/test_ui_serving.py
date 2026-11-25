"""The dashboard serves the built Svelte UI when present and keeps the legacy page reachable."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.dashboard.backend import main


def test_root_serves_built_ui_when_available(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<html><title>MIRA new ui</title></html>", encoding="utf-8")
    (tmp_path / "favicon.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    monkeypatch.setattr(main, "UI_DIST_DIR", tmp_path)
    monkeypatch.delenv("MIRA_DASHBOARD_UI", raising=False)
    with TestClient(main.app) as client:
        assert "MIRA new ui" in client.get("/").text
        assert client.get("/favicon.svg").headers["content-type"].startswith("image/svg+xml")
        assert "MIRA" in client.get("/legacy").text


def test_root_falls_back_to_legacy_without_a_build(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UI_DIST_DIR", tmp_path)
    with TestClient(main.app) as client:
        response = client.get("/")
        assert response.status_code == 200 and "MIRA new ui" not in response.text
        assert client.get("/favicon.svg").status_code == 404


def test_legacy_override_wins_even_with_a_build(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<html>MIRA new ui</html>", encoding="utf-8")
    monkeypatch.setattr(main, "UI_DIST_DIR", tmp_path)
    monkeypatch.setenv("MIRA_DASHBOARD_UI", "legacy")
    with TestClient(main.app) as client:
        assert "MIRA new ui" not in client.get("/").text


def test_status_reports_model_and_configs():
    with TestClient(main.app) as client:
        status = client.get("/api/status").json()
        assert status["model_name"] is None and status["camera_config"] is None and status["model_config"] is None
