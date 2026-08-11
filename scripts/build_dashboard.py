from __future__ import annotations

import argparse
import html
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.dashboard import aggregate_dashboard, load_events
from app.cli import configure_utf8_stdio


def _series(values: dict[str, int | float], unit: str = "") -> str:
    if not values:
        return '<div class="series empty">No data in this window</div>'
    maximum = max(float(value) for value in values.values()) or 1.0
    bars = "".join(
        f'<div class="bar" title="{html.escape(minute)}: {value}{unit}" '
        f'style="height:{max(4, float(value) / maximum * 64):.1f}px"></div>'
        for minute, value in values.items()
    )
    return f'<div class="series">{bars}</div>'


def render(metrics: dict, source: Path) -> str:
    latency = metrics["latency"]
    traffic = metrics["traffic"]
    errors = metrics["errors"]
    cost = metrics["cost"]
    tokens = metrics["tokens"]
    quality = metrics["quality"]
    breakdown = html.escape(json.dumps(errors["breakdown"], ensure_ascii=False))
    cards = [
        ("Latency percentiles", f'P50 {latency["p50_ms"]:.0f} · P95 {latency["p95_ms"]:.0f} · P99 {latency["p99_ms"]:.0f} ms', "", latency["p95_ms"] <= 3000, "P95 ≤ 3000 ms"),
        ("Request traffic", f'{traffic["request_count"]} requests · {traffic["rate_per_minute"]:.2f}/min average', _series(traffic["count_by_minute"], " requests"), traffic["rate_per_minute"] >= 1, "≥ 1 request/min"),
        ("Error rate and breakdown", f'{errors["error_rate_pct"]:.2f}% · {breakdown}', "", errors["error_rate_pct"] <= 2, "≤ 2%"),
        ("Cost over time", f'${cost["total_usd"]:.6f}', _series(cost["sum_by_minute"], " USD"), cost["total_usd"] <= 2.5, "≤ $2.50"),
        ("Input and output tokens", f'Input {tokens["input_total"]} · Output {tokens["output_total"]}', "", max(tokens["input_total"], tokens["output_total"]) <= 50000, "each field ≤ 50,000 tokens"),
        ("Quality proxy", f'{quality["average"]:.2f}', "", quality["average"] >= 0.75, "≥ 0.75"),
    ]
    card_html = "".join(
        f'<section class="card {"ok" if passed else "alert"}"><h2>{title}</h2><div class="value">{value}</div>{series}<div class="threshold">Threshold: {threshold}</div></section>'
        for title, value, series, passed, threshold in cards
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="30">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Day 13 AI Observability</title>
<style>body{{font:16px system-ui;margin:0;background:#0b1020;color:#eef2ff}}main{{max-width:1100px;margin:auto;padding:32px}}header{{display:flex;justify-content:space-between;align-items:end}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-top:24px}}.card{{background:#18213b;border:1px solid #33436b;border-left:6px solid;padding:20px;border-radius:12px}}.ok{{border-left-color:#38d996}}.alert{{border-left-color:#ff667a}}h1,h2{{margin:0 0 12px}}h2{{font-size:1rem;color:#aab7d8}}.value{{font-size:1.55rem;font-weight:700}}.threshold,small,.empty{{color:#aab7d8}}.threshold{{margin-top:12px}}.series{{height:70px;display:flex;align-items:end;gap:3px;margin-top:14px;border-bottom:1px solid #53658f}}.bar{{flex:1;min-width:3px;max-width:18px;background:#6ea8fe;border-radius:3px 3px 0 0}}.empty{{align-items:center;border:0}}</style></head>
<body><main><header><div><h1>Day 13 AI Observability</h1><small>Source: {html.escape(str(source))}</small></div><div>Last 60 minutes · refresh 30s</div></header><div class="grid">{card_html}</div></main></body></html>"""


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Build the six-panel observability dashboard")
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "submission" / "evidence" / "dashboard.html")
    parser.add_argument("--watch", action="store_true", help="Rebuild every 30 seconds until Ctrl+C")
    args = parser.parse_args()
    try:
        while True:
            metrics = aggregate_dashboard(load_events(args.logs, window_minutes=60))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(render(metrics, args.logs), encoding="utf-8")
            print(f"Dashboard written to {args.output} (6/6 panels, 60-minute window).")
            if not args.watch:
                break
            time.sleep(30)
    except KeyboardInterrupt:
        print("Dashboard watcher stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
