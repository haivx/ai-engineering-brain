# Eval

Muốn biết một model "đủ tốt" cho việc của mình hay không → phải đo, đừng đoán.

## Cạm bẫy: benchmark public
"Model X ngang o4-mini trên MMLU" chỉ cho một *prior* thô (model không phải đồ bỏ).
Nó KHÔNG trả lời được: "model này có đủ tốt cho task CỦA TÔI không?"
Benchmark đo bài toán chung; eval của bạn phải đo đúng task của bạn.

## Cách làm: eval set nhỏ từ chính task của mình
15–30 case đại diện cho việc hay làm là đủ thấy khác biệt.
Với mỗi case, định nghĩa "đạt" nghĩa là gì TRƯỚC khi chạy.
Hạ tầng có sẵn: LiteLLM giữ nguyên messages, chỉ đổi `model` string → chạy cùng bộ prompt qua nhiều model.

## "Chất lượng" với coding/agent = thứ CHẠY ĐƯỢC, không phải cảm tính
Chấm tự động bằng code, mới scale được:
- **Code chạy / pass test?** — binary, không cãi được. Sinh code → chạy pytest → đếm pass rate.
- **Structured output đúng schema?** — Pydantic `model_validate_json()` pass hay fail? Đếm tỉ lệ.
- **Tool-calling đúng?** — đúng tool, đúng tham số, đúng thứ tự? Chỗ model rẻ hay rơi nhất.
- **Instruction-following?** — bảo "chỉ JSON, không preamble" nó có nghe không?

## Task chủ quan (viết lách, giải thích) → LLM-as-judge
Đưa output cho một model mạnh chấm theo rubric, hoặc so đôi A/B.
Cảnh báo bias: judge thiên vị câu dài, thiên vị output cùng dòng model. Điểm judge chỉ là tín hiệu, không phải chân lý.

## Kỳ vọng thực tế
- Extraction / phân loại / format cố định → model rẻ thường NGANG frontier, dùng nó.
- Reasoning nhiều bước / agent loop dài → frontier bỏ xa (sai số cộng dồn).
