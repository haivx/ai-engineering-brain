# Playbook: dựng eval set tối giản

Mục tiêu: so cùng một task qua nhiều model, chấm tự động, không cảm tính.

## Các bước
1. Thu 15–30 case đại diện cho việc bạn HAY làm (input + tiêu chí "đạt" định nghĩa trước).
2. Một file cases (json/yaml). Mỗi case: prompt + cách kiểm tra kết quả.
3. Một vòng lặp: với mỗi model string, gọi qua LiteLLM cùng bộ prompt, thu output.
4. Chấm tự động theo loại:
   - Code → chạy test, đếm pass rate.
   - Structured output → Pydantic validate, đếm tỉ lệ parse pass.
   - Tool-calling → so tool/tham số kỳ vọng.
   - Chủ quan → LLM-as-judge (rubric hoặc so đôi A/B), nhớ điểm judge chỉ là tín hiệu.
5. In bảng so sánh: model × (pass rate, giá, tốc độ).
6. Lưu kết quả vào experiments/ — đây là data thật của BẠN, không tra Google được.

## Nguyên tắc
Đo đừng đoán. Prior từ benchmark public không thay được eval trên task thật của bạn.
