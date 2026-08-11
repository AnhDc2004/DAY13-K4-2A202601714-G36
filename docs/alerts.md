# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

Ba alert dưới đây tương ứng 1-1 với ba kịch bản incident dựng sẵn trong `app/incidents.py`
(`rag_slow`, `tool_fail`, `cost_spike`), có thể tái hiện bất cứ lúc nào bằng
`python scripts/inject_incident.py --scenario <tên>` để lấy evidence.

Đã tái hiện cả ba trên máy local (uvicorn + `scripts/load_test.py`) để kiểm chứng điều kiện
alert có ý nghĩa trên dữ liệu thật, không chỉ số suy đoán:

| Scenario | Baseline (`/metrics`) | Khi bật incident | Đọc được gì |
|---|---|---|---|
| `rag_slow` | latency ~155ms/request | client-side latency ~13000ms/request | Vượt xa threshold 3000ms → alert 1 sẽ nổ |
| `tool_fail` | `error_rate_pct: 0.0`, `error_count: 0` | `error_rate_pct: 50.0`, `error_breakdown: {"RuntimeError": 10}` | Vượt xa threshold 2% → alert 2 sẽ nổ |
| `cost_spike` | `avg_cost_usd: 0.0022`, `tokens_out_total` +141/req | `avg_cost_usd: 0.0052` (~2.4x), tokens_out +683/req (~4.8x) | Cost/request tăng mạnh, đủ để chạm threshold $2.5 nếu duy trì ở traffic thật |

## Alert 1

- Tên: HighLatencyP95
- Severity: High
- SLI/SLO liên quan: `latency_p95_ms` trong `config/slo.yaml` (objective 3000ms, target 99.5%);
  khớp threshold panel Latency trong `config/dashboard.yaml`.
- Điều kiện và thời gian duy trì: `p95(response_sent.latency_ms) > 3000ms`, đo trên cửa sổ
  trượt 5 phút, duy trì liên tục >= 5 phút (tránh false positive do một request đơn lẻ chậm).
- Ảnh hưởng tới người dùng: Chat trả lời chậm rõ rệt, có thể chạm timeout phía client;
  trải nghiệm "monitoring"/RAG-heavy feature bị ảnh hưởng nặng nhất.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Latency trên dashboard (`submission/evidence/dashboard.html` hoặc `python scripts/build_dashboard.py`)
     để xác định mốc thời gian P95 bắt đầu vượt ngưỡng và feature nào bị ảnh hưởng.
  2. Gọi `GET /metrics` hoặc mở trace Langfuse trong đúng khoảng thời gian đó, tìm request có
     latency cao nhất, so sánh thời lượng từng span (đặc biệt span retrieve docs/RAG).
  3. Lấy `correlation_id` của trace đó, grep trong `data/logs.jsonl` để xem log
     `request_received` → `response_sent` có field nào bất thường (vd. `doc_count`, retries).
- Mitigation tạm thời: Nếu do incident practice/challenge đang bật, tắt bằng
  `python scripts/inject_incident.py --scenario rag_slow --disable`. Nếu là sự cố thật,
  giảm `--concurrency` phía client hoặc tạm chuyển traffic sang cache/fallback response
  trong lúc chờ fix root cause ở tầng retrieval.
- Owner: Le Huy Hoang (SRE & Alerts Engineer)

## Alert 2

- Tên: ElevatedErrorRate
- Severity: Critical
- SLI/SLO liên quan: `error_rate_pct` trong `config/slo.yaml` (objective 2%, target 99.0%);
  khớp threshold panel Errors trong `config/dashboard.yaml`.
- Điều kiện và thời gian duy trì: `count(request_failed) / count(request_received) * 100 > 2%`,
  duy trì liên tục >= 5 phút. Mẫu số `request_received` được ghi cho cả request bị từ chối
  trước khi vào `/chat` (422/404/500 sớm) nhờ `_ensure_request_received` trong `app/main.py`,
  nên tỉ lệ này phản ánh đúng trải nghiệm người dùng thật, không chỉ lỗi trong agent.
- Ảnh hưởng tới người dùng: Một phần request nhận lỗi 4xx/5xx thay vì câu trả lời,
  mất niềm tin vào tính ổn định của API.
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Errors (breakdown theo `error_type`) trên dashboard để biết loại lỗi nào
     tăng đột biến và tăng từ mốc thời gian nào.
  2. Gọi `GET /metrics` xem `error_breakdown`, đối chiếu với trace Langfuse có
     `request_failed`/status lỗi trong cùng khoảng thời gian.
  3. Grep `data/logs.jsonl` theo `error_type` và `correlation_id` tương ứng, đọc field
     `payload.detail` để xác định lỗi đến từ tầng nào (tool/agent hay validation).
- Mitigation tạm thời: Nếu do incident practice đang bật, tắt bằng
  `python scripts/inject_incident.py --scenario tool_fail --disable`. Nếu do prompt version
  mới gây lỗi, rollback `production` về version trước theo `docs/PROMPT_VERSIONING.md`.
- Owner: Le Huy Hoang (SRE & Alerts Engineer)

## Alert 3

- Tên: CostBudgetExceeded
- Severity: Medium
- SLI/SLO liên quan: `daily_cost_usd` trong `config/slo.yaml` (objective $2.5/cửa sổ quan sát);
  khớp threshold "total" của panel Cost trong `config/dashboard.yaml`.
- Điều kiện và thời gian duy trì: `sum(response_sent.cost_usd)` trong cửa sổ quan sát 60 phút
  > $2.50. Không cần "duy trì" nhiều lần vì đây là tổng tích lũy, kiểm tra mỗi lần refresh (30s).
- Ảnh hưởng tới người dùng: Không ảnh hưởng trực tiếp trải nghiệm, nhưng ảnh hưởng vận hành
  (vượt ngân sách) và thường là dấu hiệu sớm của việc token/tokens_out tăng bất thường
  (model trả lời dài hơn bình thường, hoặc bị lặp/loop).
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Cost và panel Tokens trên dashboard để biết cost tăng do tần suất request
     hay do từng request tốn nhiều token hơn (`tokens_in`/`tokens_out`).
  2. Gọi `GET /metrics`, so sánh `avg_cost_usd` hiện tại với baseline đo được lúc chạy
     `python scripts/load_test.py` (baseline ~$0.002/request).
  3. Mở vài trace gần nhất trong khoảng thời gian đó, xem `usage_details`/`cost_details`
     trên Langfuse để xác định request nào bất thường và feature nào liên quan.
  - Test/tái hiện thực tế: `python scripts/inject_incident.py --scenario cost_spike`.
- Mitigation tạm thời: Nếu do incident practice đang bật, tắt bằng
  `python scripts/inject_incident.py --scenario cost_spike --disable`. Nếu là sự cố thật,
  giới hạn `--concurrency` phía client hoặc tạm giới hạn độ dài câu trả lời qua prompt
  candidate đã kiểm chứng trong `docs/PROMPT_VERSIONING.md`.
- Owner: Le Huy Hoang (SRE & Alerts Engineer)
