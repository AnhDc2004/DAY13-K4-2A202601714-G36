# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: G36
- Repository URL: https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36
- Commit SHA cuối: 
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

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: `submission/evidence/dashboard.html` (cửa sổ 60 phút, refresh 30 giây, có threshold và time series traffic/cost theo phút)
- SLO đã chọn và lý do:
- Alert rules và runbook:

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
| Trần Minh Hạnh | Tính `error_rate_pct`; tổng hợp 6 nhóm metrics từ JSONL; dashboard 60 phút, refresh 30 giây, threshold và time series theo phút; unit/integration tests | Bổ sung SHA/PR sau khi commit | Phân biệt request attempt với success/error; tính percentile, error rate và bucket metrics theo thời gian |
| Lê Huy Hoàng | SRE & Alerts Engineer | | |
| Nguyễn Thành Huy | QA & Chief Investigator | | |
