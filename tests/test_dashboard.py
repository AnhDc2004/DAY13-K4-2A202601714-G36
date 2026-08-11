from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from app.dashboard import aggregate_dashboard, load_events


def test_dashboard_aggregates_all_six_groups() -> None:
    first_minute = "2026-08-11T07:00:00+00:00"
    second_minute = "2026-08-11T07:01:00+00:00"
    events = [
        {"event": "request_received", "ts": first_minute},
        {"event": "response_sent", "ts": first_minute, "latency_ms": 100, "cost_usd": 0.1, "tokens_in": 10, "tokens_out": 5, "quality_score": 0.8},
        {"event": "request_received", "ts": second_minute},
        {"event": "request_failed", "ts": second_minute, "error_type": "TimeoutError"},
    ]

    result = aggregate_dashboard(events)

    assert set(result) == {"latency", "traffic", "errors", "cost", "tokens", "quality"}
    assert result["traffic"]["request_count"] == 2
    assert list(result["traffic"]["count_by_minute"].values()) == [1, 1]
    assert result["errors"]["error_rate_pct"] == 50.0
    assert result["errors"]["breakdown"] == {"TimeoutError": 1}
    assert result["tokens"] == {"input_total": 10, "output_total": 5}
    assert list(result["cost"]["sum_by_minute"].values()) == [0.1]
    assert result["quality"]["average"] == 0.8


def test_load_events_uses_60_minute_window_and_skips_bad_lines(tmp_path) -> None:
    now = datetime.now(timezone.utc)
    path = tmp_path / "logs.jsonl"
    lines = [
        json.dumps({"event": "request_received", "ts": now.isoformat()}),
        json.dumps({"event": "request_received", "ts": (now - timedelta(minutes=61)).isoformat()}),
        "not-json",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")

    events = load_events(path)

    assert len(events) == 1
