from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from .metrics import percentile


def load_events(path: Path, window_minutes: int = 60) -> list[dict[str, Any]]:
    """Load valid JSON log events within the requested UTC time window."""
    if not path.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            timestamp = datetime.fromisoformat(str(event["ts"]).replace("Z", "+00:00"))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
        if timestamp >= cutoff:
            events.append(event)
    return events


def _numbers(events: Iterable[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for event in events:
        value = event.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.append(float(value))
    return values


def _minute_key(event: dict[str, Any]) -> str | None:
    try:
        timestamp = datetime.fromisoformat(str(event["ts"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        return None
    return timestamp.astimezone(timezone.utc).replace(second=0, microsecond=0).isoformat()


def _count_by_minute(events: Iterable[dict[str, Any]]) -> dict[str, int]:
    buckets: Counter[str] = Counter()
    for event in events:
        minute = _minute_key(event)
        if minute:
            buckets[minute] += 1
    return dict(sorted(buckets.items()))


def _sum_by_minute(events: Iterable[dict[str, Any]], field: str) -> dict[str, float]:
    buckets: dict[str, float] = {}
    for event in events:
        minute = _minute_key(event)
        value = event.get(field)
        if minute and isinstance(value, (int, float)) and not isinstance(value, bool):
            buckets[minute] = buckets.get(minute, 0.0) + float(value)
    return {minute: round(value, 6) for minute, value in sorted(buckets.items())}


def aggregate_dashboard(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply the six aggregation rules declared in config/dashboard.yaml."""
    received = [event for event in events if event.get("event") == "request_received"]
    failed = [event for event in events if event.get("event") == "request_failed"]
    completed = [event for event in events if event.get("event") == "response_sent"]

    latencies = _numbers(completed, "latency_ms")
    costs = _numbers(completed, "cost_usd")
    tokens_in = _numbers(completed, "tokens_in")
    tokens_out = _numbers(completed, "tokens_out")
    quality = _numbers(completed, "quality_score")
    error_breakdown = Counter(
        str(event.get("error_type", "UnknownError")) for event in failed
    )

    request_count = len(received)
    traffic_by_minute = _count_by_minute(received)
    cost_by_minute = _sum_by_minute(completed, "cost_usd")
    return {
        "latency": {
            "p50_ms": percentile(latencies, 50),
            "p95_ms": percentile(latencies, 95),
            "p99_ms": percentile(latencies, 99),
        },
        "traffic": {
            "request_count": request_count,
            "rate_per_minute": round(request_count / 60, 2),
            "count_by_minute": traffic_by_minute,
        },
        "errors": {
            "error_count": len(failed),
            "error_rate_pct": round(len(failed) / request_count * 100, 2)
            if request_count
            else 0.0,
            "breakdown": dict(error_breakdown),
        },
        "cost": {
            "total_usd": round(sum(costs), 6),
            "sum_by_minute": cost_by_minute,
        },
        "tokens": {
            "input_total": int(sum(tokens_in)),
            "output_total": int(sum(tokens_out)),
        },
        "quality": {"average": round(mean(quality), 4) if quality else 0.0},
    }
