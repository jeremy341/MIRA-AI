"""Export routes and report rendering tests for dashboard v2."""

from __future__ import annotations

import csv
import io
import re
from html.parser import HTMLParser
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.dashboard.backend.main import app
from src.dashboard.backend.v1.state import get_db


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def _insert_session(
    session_id: str = "session-12345678",
    *,
    name: str = "Sample session",
    started_at: float = 1_000.0,
    ended_at: float | None = 1_010.0,
    model_name: str | None = "yolo11n.pt",
    source: str = "camera",
    notes: str | None = None,
    config: str | None = '{"confidence": 0.25}',
) -> None:
    get_db().execute(
        "INSERT INTO sessions (id, name, source, model_name, status, started_at_ts, ended_at_ts, config_json, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            session_id,
            name,
            source,
            model_name,
            "active" if ended_at is None else "completed",
            started_at,
            ended_at,
            config,
            notes,
        ),
    )


def _insert_detection(
    session_id: str,
    *,
    ts: float,
    class_name: str = "glass",
    confidence: float = 0.9,
    frame_index: int = 0,
    track_id: int | None = 7,
) -> None:
    get_db().execute(
        "INSERT INTO detections "
        "(session_id, ts, frame_index, class_name, confidence, x1, y1, x2, y2, track_id) "
        "VALUES (?, ?, ?, ?, ?, 1, 2, 30, 40, ?)",
        (session_id, ts, frame_index, class_name, confidence, track_id),
    )


def test_csv_has_contract_header_and_utc_detection_rows(client):
    _insert_session()
    _insert_detection("session-12345678", ts=1_000.125, frame_index=3)

    response = client.get("/api/v1/sessions/session-12345678/export.csv")

    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == [
        "ts",
        "offset_seconds",
        "frame_index",
        "class_name",
        "confidence",
        "x1",
        "y1",
        "x2",
        "y2",
        "track_id",
    ]
    assert rows[1] == ["1970-01-01T00:16:40.125000+00:00", "0.125", "3", "glass", "0.9", "1", "2", "30", "40", "7"]
    assert response.headers["content-type"].startswith("text/csv")


def test_csv_attachment_filename_is_ascii_and_path_safe(client):
    session_id = "a1b2c3d4e5f6"
    _insert_session(session_id, name="../../Glass: session\u2603")

    response = client.get(f"/api/v1/sessions/{session_id}/export.csv")

    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    filename = re.search(r'filename="([^"]+)"', disposition).group(1)
    assert filename == "glass-session-a1b2c3d4.csv"
    assert filename.isascii()
    assert "/" not in filename and "\\" not in filename and ".." not in filename


@pytest.mark.parametrize("formula", ["=1+1", "+SUM(1,1)", "-1+2", "@cmd"])
def test_csv_prefixes_formula_like_text_cells(client, formula):
    session_id = "formula-test"
    _insert_session(session_id)
    _insert_detection(session_id, ts=1_001, class_name=formula)

    response = client.get(f"/api/v1/sessions/{session_id}/export.csv")
    row = next(csv.DictReader(io.StringIO(response.text)))

    assert row["class_name"] == f"'{formula}"


def test_json_export_uses_contract_session_fields_and_includes_metrics(client):
    session_id = "json-session"
    _insert_session(session_id, notes="Checked by hand")
    _insert_detection(session_id, ts=1_002, confidence=0.8)
    get_db().execute(
        "INSERT INTO metrics (session_id, ts, fps, latency_ms, cpu_percent, memory_percent, temperature_c) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, 1_003, 12.5, 80, 25, 40, 51.2),
    )

    response = client.get(f"/api/v1/sessions/{session_id}/export.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "attachment" in response.headers["content-disposition"]
    payload = response.json()
    assert set(payload) == {"session", "class_counts", "detections", "metrics"}
    assert set(payload["session"]) == {
        "id",
        "name",
        "source",
        "model_name",
        "status",
        "started_at",
        "ended_at",
        "duration_seconds",
        "total_detections",
        "class_counts",
        "avg_confidence",
        "config",
        "notes",
    }
    assert payload["session"]["config"] == {"confidence": 0.25}
    assert payload["session"]["notes"] == "Checked by hand"
    assert payload["session"]["total_detections"] == 1
    assert payload["class_counts"]["glass"] == 1
    assert payload["detections"][0]["ts"] == "1970-01-01T00:16:42+00:00"
    assert payload["detections"][0]["bbox"] == [1, 2, 30, 40]
    assert payload["metrics"][0]["ts"] == "1970-01-01T00:16:43+00:00"
    assert payload["metrics"][0]["fps"] == 12.5


def test_report_escapes_user_text_and_has_no_external_resources(client):
    session_id = "report-xss"
    _insert_session(session_id, name="<script>alert(1)</script>", notes="<img src=x onerror=alert(1)>")
    _insert_detection(session_id, ts=1_001)

    response = client.get(f"/api/v1/sessions/{session_id}/report.html")

    assert response.status_code == 200
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;img src=x onerror=alert(1)&gt;" in response.text
    assert "http://" not in response.text
    assert "https://" not in response.text
    assert "Session counts describe this run only and are not real-world sorting accuracy." in response.text
    assert "@page { size: A4; margin: 12mm }" in response.text


def test_report_download_sets_attachment_header(client):
    _insert_session("report-download")

    response = client.get("/api/v1/sessions/report-download/report.html?download=1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["content-disposition"].endswith('.html"')


def test_empty_session_report_has_clear_empty_state(client):
    session_id = "empty-session"
    _insert_session(session_id)

    response = client.get(f"/api/v1/sessions/{session_id}/report.html")

    assert response.status_code == 200
    assert "No detections recorded" in response.text
    assert "Total detections" in response.text
    assert ">0</strong>" in response.text


def test_active_session_report_uses_latest_recorded_timestamp(client):
    session_id = "active-session"
    _insert_session(session_id, started_at=2_000, ended_at=None)
    _insert_detection(session_id, ts=2_006)
    get_db().execute("INSERT INTO metrics (session_id, ts, fps) VALUES (?, ?, ?)", (session_id, 2_010, 8.0))

    response = client.get(f"/api/v1/sessions/{session_id}/report.html")

    assert response.status_code == 200
    assert "10 seconds" in response.text
    assert "Active" in response.text


def test_missing_session_exports_return_404(client):
    for suffix in ("export.csv", "export.json", "report.html"):
        response = client.get(f"/api/v1/sessions/missing/{suffix}")
        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()


def test_csv_streams_thousands_of_detections(client):
    session_id = "large-session"
    _insert_session(session_id)
    get_db().executemany(
        "INSERT INTO detections (session_id, ts, frame_index, class_name, confidence, x1, y1, x2, y2, track_id) "
        "VALUES (?, ?, ?, ?, ?, 1, 2, 3, 4, NULL)",
        ((session_id, 1_000 + index / 30, index, "plastic", 0.75) for index in range(3_000)),
    )

    response = client.get(f"/api/v1/sessions/{session_id}/export.csv")

    rows = list(csv.reader(io.StringIO(response.text)))
    assert response.status_code == 200
    assert len(rows) == 3_001
    assert rows[-1][2:5] == ["2999", "plastic", "0.75"]


class _SvgCounter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.charts: list[str | None] = []

    def handle_starttag(self, tag, attrs):
        if tag == "svg":
            attributes = dict(attrs)
            self.charts.append(attributes.get("data-chart"))


def test_report_html_parses_and_has_one_svg_per_chart(client):
    session_id = "chart-session"
    _insert_session(session_id)
    _insert_detection(session_id, ts=1_001)

    response = client.get(f"/api/v1/sessions/{session_id}/report.html")
    parser = _SvgCounter()
    parser.feed(response.text)
    parser.close()

    assert parser.charts == ["class-counts", "detections-over-time"]


def test_csv_route_accepts_url_encoded_id(client):
    session_id = "simple-id"
    _insert_session(session_id)

    response = client.get(f"/api/v1/sessions/{quote(session_id, safe='')}/export.csv")

    assert response.status_code == 200
