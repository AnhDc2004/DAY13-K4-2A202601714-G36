# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: G36
- Repository URL: https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36
- Commit SHA cuối: [2619fbc](https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36/commit/2619fbc) (cập nhật lại thành commit thực sự cuối cùng ngay trước khi nộp bài)
- Thành viên và vai trò: 

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: **100/100** — sau khi gộp phần A (correlation ID + enrichment) + phần B (PII scrubbing), cả 4 hạng mục đều PASSED (Basic JSON schema, Correlation ID propagation, Log enrichment, PII scrubbing).
- Tổng số traces:
- Số PII leak còn lại: **0** — `validate_logs.py` báo `Potential PII leaks detected: 0` + grep `student@|vinuni.edu.vn|0987654321|4111 1111 1111 1111|C1234567` = 0 hit (evidence: `submission/evidence/pii-redaction.txt`).
- Link/đường dẫn dashboard: `submission/evidence/dashboard.html`

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction: `submission/evidence/pii-redaction.txt` — output `validate_logs.py` (100/100, PII leaks = 0), kết quả grep raw tokens = 0, 10 correlation ID hợp lệ `req-<8hex>`, 2 dòng log mẫu có đủ enrichment và đã thay bằng `[REDACTED_*]`.
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

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

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Đinh Đức Anh | API & Middleware | [49c726b](https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36/commit/49c726b) | Correlation ID chỉ có giá trị khi được bind vào contextvars trước dòng log đầu tiên và xoá ở đầu mỗi request - nhờ vậy mọi log, kể cả request_failed sinh ra trong exception handler, đều truy ngược được về đúng một request. |
| Phan Văn Phương | Security Engineer | [524c9c6](https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36/commit/524c9c6) | Thứ tự processor structlog quyết định PII có được che trước khi ghi file; regex pattern cho dữ liệu VN (hộ chiếu, số nhà); kiểm chứng log bằng validate + grep |
| Trần Minh Hạnh | Tính `error_rate_pct`; tổng hợp 6 nhóm metrics từ JSONL; dashboard 60 phút, refresh 30 giây, threshold và time series theo phút; unit/integration tests | fbac78f | Phân biệt request attempt với success/error; tính percentile, error rate và bucket metrics theo thời gian |
| Lê Huy Hoàng | SRE & Alerts Engineer — SLO (`config/slo.yaml`), alert rules (`config/alert_rules.yaml`), runbook (`docs/alerts.md`), evidence dashboard before/after | [2619fbc](https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36/commit/2619fbc) | Alert phải symptom-based và có ngưỡng khớp với dashboard contract để không lệch số giữa các thành viên; đếm đúng mẫu số `request_received` (kể cả request bị từ chối sớm) mới ra `error_rate_pct` chính xác; khi test concurrency, latency nội bộ mỗi request không đổi nhưng latency client tăng vọt do event loop bị chặn bởi `time.sleep()` — hiểu rõ khác biệt giữa symptom nội bộ và symptom người dùng cảm nhận. |
| Nguyễn Thành Huy | QA & Chief Investigator | | |
