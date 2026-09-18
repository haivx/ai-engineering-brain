# Playbook: dựng một bộ eval tối giản

Mục tiêu: so sánh cùng một tác vụ trên nhiều model, chấm điểm tự động, không cảm tính.

## Các bước
1. Thu thập 15–30 case đại diện cho những gì bạn THỰC SỰ làm (input + tiêu chí "pass" định nghĩa trước).
2. Một file cases (json/yaml). Mỗi case: prompt + cách kiểm tra kết quả.
3. Một vòng lặp: với mỗi chuỗi model, gọi qua LiteLLM với cùng bộ prompt và thu output.
4. Chấm điểm tự động, theo từng loại:
   - Code → chạy test, đếm pass rate.
   - Structured output → validate bằng Pydantic, đếm tỉ lệ parse thành công.
   - Tool-calling → so với tool/tham số kỳ vọng.
   - Chủ quan → LLM-as-judge (rubric hoặc A/B từng cặp); nhớ rằng điểm của judge chỉ là một tín hiệu.
5. In bảng so sánh: model × (pass rate, giá, tốc độ).
6. Lưu kết quả vào experiments/ — đây là dữ liệu thật CỦA BẠN, không Google ra được.
7. Ghi log mọi case dưới dạng bản ghi JSONL có cấu trúc, không phải lệnh print — mỗi dòng một bước pipeline, không phải mỗi dòng một case. Các trường: `run_id`, `case_id` (hai trường này cùng nhau giúp grep ngược từ một lỗi về đúng trace của nó), `step`, `status` (`ok`/`error` — tuyệt đối đừng gộp "trả lời sai" và "crash" vào cùng một rổ), `duration_ms`, `error`.
8. Cho mỗi giai đoạn pipeline một bản ghi riêng — một chữ "failed" ở mức case không cho bạn biết giai đoạn nào đã crash.
9. Lưu bản tóm tắt kết quả của mỗi lần chạy vào một file có tag (`results/eval_<tag>.json`) — bạn cần số liệu của lần chạy trước nằm trên đĩa, chứ không phải trôi trong màn hình terminal.

## Nguyên tắc
- Đo, đừng đoán. Một prior từ benchmark công khai không thay thế được eval trên tác vụ thật của bạn.
- Khi kiểm tra một thay đổi, hãy diff danh sách case bị lật kết quả giữa hai bản kết quả đã lưu, đừng chỉ nhìn con số tổng — một mức "+X%" có thể che giấu N case mới pass bị bù trừ bởi M case mới fail.
- Không có case nào lật kết quả trước/sau nghĩa là bộ eval không hề động tới biến số đó — hãy sửa lại bộ case, đừng báo cáo kết quả rỗng đó thành "không có regression".
- Con số pass rate cho biết hỏng bao nhiêu; log có cấu trúc cho biết hỏng ở case nào và vì sao. Giữ cả hai.
