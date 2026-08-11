# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: G36
- Repository URL: https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36
- Commit SHA cuối: `c14559b`
- Thành viên và vai trò:
  - Đinh Đức Anh - API & Middleware
  - Phan Văn Phương - Security Engineer
  - Trần Minh Hạnh - Metrics & Dashboard
  - Lê Huy Hoàng - SRE & Alerts Engineer
  - Nguyễn Thành Huy - QA & Chief Investigator

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: **100/100**
- Kết quả `validate_dashboard.py`: **HỢP LỆ: 6/6 panel có trong dashboard contract.**
- Tổng số log records trong evidence hiện tại: **21**
- Số correlation ID khác nhau: **10**
- Số PII leak phát hiện: **0**
- Tổng số trace IDs được ghi trong harness kiểm chứng propagation cục bộ: **10**

## 3. Logging và tracing

- Evidence correlation ID và log enrichment: `submission/evidence/validate-logs.txt`
- Evidence PII redaction: `submission/evidence/pii-redaction.txt`
- Evidence trace list 10 IDs: `submission/evidence/trace-list.txt`
- Evidence trace table screenshot: `submission/evidence/dashboard-traces.png`
- Evidence trace waterfall screenshot: `submission/evidence/dashboard-traces-wallterfall.png`
- Evidence trace/challenge run có `trace_id` và `correlation_id`: `submission/evidence/challenge-investigation.txt`
- Span hierarchy đã được mở rộng cho sub-component:
  - `rag.retrieve`
  - `llm.generate`
- Mình đã giữ metadata prompt ở cả trace và generation để đối chiếu version/label:
  - `prompt_name`
  - `prompt_label`
  - `prompt_version`
  - `prompt_source`

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Contract prompt trong repo: `Feature={{feature}}`, `Docs={{docs}}`, `Question={{message}}`
- Trace/generation metadata đã khóa trong test: `tests/test_agent_prompt_trace.py`
- Ghi chú:
  - code lưu `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`
  - khi Langfuse không sẵn sàng, app dùng local fallback nhưng vẫn giữ metadata để audit

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.` (evidence: `submission/evidence/validate-dashboard.txt`)
- Kết quả `validate_logs.py` chạy lại sau khi có đủ traffic baseline + 3 incident: **100/100**, 86 log record, 46 correlation ID hợp lệ, PII leak = 0 (evidence: `submission/evidence/validate-logs.txt`).
- Evidence dashboard: `submission/evidence/dashboard.html` (cửa sổ 60 phút, refresh 30 giây, có threshold và time series traffic/cost theo phút) và 4 ảnh so sánh trước/sau incident:
  - `dashboard-baseline.png` — 6 panel bình thường, tất cả đạt threshold.
  - `dashboard-alert-rag_slow.png` — P95 latency 150ms → 2651ms (tăng ~17 lần); vẫn dưới ngưỡng 3000ms trong batch test 10 request nên panel còn xanh, nhưng số liệu cho thấy tín hiệu rõ ràng và đủ để trace/log điều tra tiếp.
  - `dashboard-alert-tool_fail.png` — error rate 0% → 100% (`RuntimeError` x10), panel Errors và Quality chuyển đỏ.
  - `dashboard-alert-cost_spike.png` — cost/10 request $0.0225 → $0.0719 (~3.2x), output tokens ~3.3x, chưa chạm ngưỡng $2.5 vì cửa sổ test ngắn nhưng xu hướng rõ ràng.
- SLO đã chọn và lý do (`config/slo.yaml`): giữ nguyên 4 objective khớp với threshold trong `config/dashboard.yaml`/`app/dashboard.py` để không lệch contract chấm điểm:
  - `latency_p95_ms` ≤ 3000ms, target 99.5% — baseline đo thực tế chỉ ~155ms nên còn nhiều biên độ cho tail latency, nhưng vẫn đủ nhạy để bắt được incident `rag_slow`.
  - `error_rate_pct` ≤ 2%, target 99.0% — mẫu số dùng `request_received` được đếm cho cả request bị từ chối trước `/chat` (422/500 sớm, nhờ hàm `_ensure_request_received` trong `app/main.py`) nên phản ánh đúng tỉ lệ thất bại người dùng gặp phải.
  - `daily_cost_usd` ≤ $2.5 — objective khớp threshold "total" của panel Cost, tính trên cửa sổ quan sát 60 phút chứ không phải chi phí theo ngày lịch thực tế.
  - `quality_score_avg` ≥ 0.75, target 95.0% — khớp threshold mean `quality_score` của panel Quality.
- Alert rules và runbook (`config/alert_rules.yaml` + `docs/alerts.md`): 3 alert symptom-based, mỗi alert map 1-1 với một kịch bản incident thực nghiệm được để có thể tái hiện bất cứ lúc nào bằng `python scripts/inject_incident.py --scenario <tên>`:
  1. **HighLatencyP95** (severity high) — `p95(latency_ms) > 3000ms` duy trì ≥5 phút, test bằng `rag_slow`.
  2. **ElevatedErrorRate** (severity critical) — `error_rate_pct > 2%` duy trì ≥5 phút, test bằng `tool_fail`.
  3. **CostBudgetExceeded** (severity medium) — tổng `cost_usd` trong cửa sổ 60 phút > $2.5, test bằng `cost_spike`.
  Mỗi alert trong `docs/alerts.md` có đủ severity, SLI/SLO liên quan, điều kiện + thời gian duy trì, ảnh hưởng người dùng, 3 bước kiểm tra đầu tiên, mitigation tạm thời và owner.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1`
- Incident chính: `rag_slow`
- Triệu chứng:
  - latency p95 tăng lên khoảng `2653 ms`
  - vượt ngưỡng challenge `2000 ms`
  - traffic vẫn bình thường, error rate = `0%`
- Trace ID liên quan: `00000000000000000000000000000007`
- Correlation ID liên quan: `req-cdc06c50`
- Log line liên quan:
  - `request_received` cho câu hỏi `Explain why metrics traces and logs work together.`
  - `response_sent` cùng correlation ID, latency `2653 ms`
- Root cause:
  - `app/mock_rag.py` inject `time.sleep(2.5)` khi incident `rag_slow` bật
  - đây là nguồn làm chậm rõ ràng nhất trong waterfall
- Fix action:
  - tắt incident / xử lý đường truy vấn RAG chậm
  - ưu tiên nhìn vào span `rag.retrieve` trước khi đổ lỗi cho LLM
- Preventive measure:
  - alert theo p95 latency thay vì average
  - dùng correlation ID nối metric -> trace -> log
  - giữ trace sub-component để đọc waterfall nhanh hơn

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Đinh Đức Anh | API & Middleware | [49c726b](https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36/commit/49c726b) | Correlation ID chỉ có giá trị khi được bind vào contextvars trước dòng log đầu tiên và xoá ở đầu mỗi request - nhờ vậy mọi log, kể cả request_failed sinh ra trong exception handler, đều truy ngược được về đúng một request. |
| Phan Văn Phương | Security Engineer | [524c9c6](https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36/commit/524c9c6) | Thứ tự processor structlog quyết định PII có được che trước khi ghi file; regex pattern cho dữ liệu VN (hộ chiếu, số nhà); kiểm chứng log bằng validate + grep |
| Trần Minh Hạnh | Metrics & Dashboard | [fbac78f](https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36/commit/fbac78f) | Phân biệt request attempt với success/error; tính percentile, error rate và bucket metrics theo thời gian |
| Lê Huy Hoàng | SRE & Alerts Engineer | [2619fbc](https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36/commit/2619fbc) | Alert phải symptom-based và có ngưỡng khớp với dashboard contract để không lệch số giữa các thành viên; đếm đúng mẫu số `request_received` (kể cả request bị từ chối sớm) mới ra `error_rate_pct` chính xác; khi test concurrency, latency nội bộ mỗi request không đổi nhưng latency client tăng vọt do event loop bị chặn bởi `time.sleep()` - hiểu rõ khác biệt giữa symptom nội bộ và symptom người dùng cảm nhận. |
| Nguyễn Thành Huy | QA & Chief Investigator | [c14559b](https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36/commit/c14559b) | Load test + trace propagation + challenge evidence phải đi cùng nhau để kết luận root cause có cơ sở. |
