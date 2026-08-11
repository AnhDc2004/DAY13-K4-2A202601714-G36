from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app import metrics
from app.main import app


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert response_event["quality_score"] == response.json()["quality_score"]


def test_invalid_chat_logs_received_before_failed_and_counts_error_rate(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    metrics.TRAFFIC = 0
    metrics.ERRORS.clear()

    with TestClient(app) as client:
        response = client.post("/chat", json={"message": "missing required fields"})

    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    relevant = [event["event"] for event in events if event["event"] in {"request_received", "request_failed"}]
    assert response.status_code == 422
    assert relevant == ["request_received", "request_failed"]
    assert metrics.snapshot()["traffic"] == 1
    assert metrics.snapshot()["error_rate_pct"] == 100.0
