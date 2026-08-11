# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: G36
- Repository URL: https://github.com/AnhDc2004/DAY13-K4-2A202601714-G36
- Commit SHA cuối: `2619fbc5b7a306810f90d9677edd4c65c9d66f1b`
- Thành viên và vai trò:
  - Đinh Đức Anh - API & Middleware
  - Phan Văn Phương - Security Engineer
  - Trần Minh Hạnh - Metrics & Dashboard
  - Lê Huy Hoàng - SRE & Alerts Engineer
  - Nguyễn Thành Huy - QA & Chief Investigator

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: **100/100**
- Tổng số log records trong evidence hiện tại: **21**
- Số correlation ID khác nhau: **10**
- Số PII leak phát hiện: **0**
- Tổng số trace IDs được ghi trong harness kiểm chứng propagation cục bộ: **10**

## 3. Logging và tracing

- Evidence correlation ID và log enrichment: `submission/evidence/validate-logs.txt`
- Evidence PII redaction: `submission/evidence/pii-redaction.txt`
- Evidence trace propagation 10 IDs: `submission/evidence/trace-list.txt`
- Evidence trace waterfall/challenge run có `trace_id` và `correlation_id`: `submission/evidence/challenge-investigation.txt`
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

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Dashboard runtime: `submission/evidence/dashboard.html`
- 6 nhóm chỉ số:
  - latency
  - traffic
  - errors
  - cost
  - tokens
  - quality
- SLO chọn trong repo:
  - latency p95 <= 3000 ms
  - error rate <= 2%
  - daily cost <= 2.5 USD
  - quality proxy >= 0.75
- Alert rules và runbook:
  - `config/alert_rules.yaml`
  - `docs/alerts.md`

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

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Đinh Đức Anh | API & Middleware | `2619fbc` | Correlation ID phải được bind ngay đầu request để log lỗi vẫn truy ngược được một request cụ thể. |
| Phan Văn Phương | Security Engineer | `2619fbc` | Scrub PII phải chạy trước khi render JSON, và regex cần cover email, phone, CCCD, passport, credit card, address. |
| Trần Minh Hạnh | Metrics & Dashboard | `2619fbc` | Error rate nên đếm trên request_received/request_failed để không đếm trùng success path. |
| Lê Huy Hoàng | SRE & Alerts Engineer | `2619fbc` | Alert tốt cần threshold, duration, severity và owner rõ ràng, kèm runbook đọc metric rồi trace rồi log. |
| Nguyễn Thành Huy | QA & Chief Investigator | `2619fbc` | Load test + trace propagation + challenge evidence phải đi cùng nhau để kết luận root cause có cơ sở. |

