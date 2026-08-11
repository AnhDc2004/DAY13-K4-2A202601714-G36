from app import metrics
from app.metrics import percentile


def setup_function() -> None:
    metrics.REQUEST_LATENCIES.clear()
    metrics.REQUEST_COSTS.clear()
    metrics.REQUEST_TOKENS_IN.clear()
    metrics.REQUEST_TOKENS_OUT.clear()
    metrics.ERRORS.clear()
    metrics.QUALITY_SCORES.clear()
    metrics.TRAFFIC = 0


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_snapshot_reports_zero_error_rate_without_traffic() -> None:
    assert metrics.snapshot()["error_rate_pct"] == 0.0


def test_snapshot_counts_successful_and_failed_requests() -> None:
    for _ in range(10):
        metrics.record_request_received()
    for _ in range(8):
        metrics.record_request(100, 0.01, 10, 5, 0.8)
    metrics.record_error("TimeoutError")
    metrics.record_error("TimeoutError")

    result = metrics.snapshot()

    assert result["traffic"] == 10
    assert result["error_count"] == 2
    assert result["error_rate_pct"] == 20.0
    assert result["error_breakdown"] == {"TimeoutError": 2}


def test_outcome_does_not_increment_traffic_twice() -> None:
    metrics.record_request_received()
    metrics.record_request(100, 0.01, 10, 5, 0.8)
    metrics.record_error("LateFailure")

    assert metrics.snapshot()["traffic"] == 1
