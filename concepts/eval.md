# Eval

Muốn biết một model có "đủ tốt" cho công việc của bạn hay không → hãy đo, đừng đoán.

## Cạm bẫy: benchmark công khai
"Model X ngang o4-mini trên MMLU" chỉ cho bạn một *prior* thô (model này không phải đồ bỏ).
Nó KHÔNG trả lời được: "model này có đủ tốt cho tác vụ CỦA TÔI không?"
Benchmark đo các bài toán chung chung; eval của bạn phải đo đúng tác vụ thật của bạn.

## Cách làm: một bộ eval nhỏ rút ra từ chính công việc của bạn
15–30 case đại diện cho những gì bạn thường làm là đủ để thấy khác biệt.
Với mỗi case, định nghĩa thế nào là "pass" TRƯỚC khi chạy.
Hạ tầng thì đã có sẵn: LiteLLM giữ nguyên messages, bạn chỉ đổi chuỗi `model` → chạy cùng một bộ prompt qua nhiều model.

## Với coding/agent, "chất lượng" = thứ CHẠY ĐƯỢC, không phải thứ đọc thấy sướng
Chấm điểm tự động bằng code — đó là cách duy nhất mở rộng được:
- **Code có chạy / có pass test không?** — nhị phân, không cãi được. Sinh code → chạy pytest → đếm pass rate.
- **Structured output có khớp schema không?** — `model_validate_json()` của Pydantic pass hay fail? Đếm tỉ lệ.
- **Tool-calling có đúng không?** — đúng tool, đúng tham số, đúng thứ tự? Đây là chỗ model rẻ hỏng nhiều nhất.
- **Instruction-following?** — bảo nó "chỉ JSON, không lời dẫn": nó có nghe không?

## Tác vụ chủ quan (viết lách, giải thích) → LLM-as-judge
Đưa output cho một model mạnh chấm theo rubric, hoặc so sánh A/B từng cặp.
Cảnh báo thiên lệch: judge thiên vị câu trả lời dài và thiên vị output từ chính dòng model của nó. Điểm của judge chỉ là một tín hiệu, không phải sự thật.

## Kỳ vọng thực tế
- Extraction / classification / định dạng cố định → model rẻ thường NGANG NGỬA model frontier; cứ dùng.
- Reasoning nhiều bước / agent loop dài → model frontier bỏ xa (compounding error).
