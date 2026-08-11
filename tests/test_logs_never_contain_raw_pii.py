from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app
from scripts import validate_logs


def test_logs_never_contain_raw_pii(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    messages = (
        "email student@vinuni.edu.vn | phone 0987654321 | card 4111 1111 1111 1111",
        "passport C1234567 | address số 12 đường Nguyễn Trãi",
    )
    with TestClient(app) as client:
        for message in messages:
            response = client.post(
                "/chat",
                json={
                    "user_id": "u-pii-test",
                    "session_id": "s-pii-test",
                    "feature": "qa",
                    "message": message,
                },
            )
            assert response.status_code == 200

    raw = log_path.read_text(encoding="utf-8")
    for leaked in (
        "student@",
        "vinuni.edu.vn",
        "0987654321",
        "4111 1111 1111 1111",
        "C1234567",
    ):
        assert leaked not in raw, f"raw PII leaked into logs: {leaked}"

    assert "REDACTED_EMAIL" in raw
    assert "REDACTED_PHONE_VN" in raw
    assert "REDACTED_CREDIT_CARD" in raw
    assert "REDACTED_PASSPORT_VN" in raw
    assert "REDACTED_ADDRESS_VN" in raw


def test_validator_reports_zero_pii_leaks_after_scrubbing(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        client.post(
            "/chat",
            json={
                "user_id": "u-pii-test",
                "session_id": "s-pii-test",
                "feature": "qa",
                "message": (
                    "email student@vinuni.edu.vn | phone 0987654321 "
                    "| card 4111 1111 1111 1111"
                ),
            },
        )

    monkeypatch.setattr(validate_logs, "LOG_PATH", log_path)
    validate_logs.main()

    output = capsys.readouterr().out
    assert "Potential PII leaks detected: 0" in output
    assert "[PASSED] PII scrubbing" in output
