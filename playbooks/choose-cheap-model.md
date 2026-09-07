# Playbook: chọn model rẻ để dùng tạm

Khi hết quota/token và cần một model thay thế nhanh.

## Các bước
1. Mở **llm-stats.com**, lọc theo trục cần (coding / cheapest / open-weight).
2. Đối chiếu giá THẬT trên **openrouter.ai** (giá đổi liên tục, luôn check lại tại đây).
3. Phân loại task đang cần (xem concepts/model-tiers.md):
   - Lặt vặt / boilerplate / extraction → chọn model open rẻ nhất còn "capable".
   - Coding cần chất lượng → model coding open khá + context đủ dài.
   - Việc khó thật → cân nhắc KHÔNG hạ tầng (đợi/nạp thêm).
4. Trong LiteLLM: chỉ đổi `MODEL` string. Không sửa gì khác.
5. Nếu là việc quan trọng → chạy qua eval set (playbooks/build-eval-set.md) trước khi tin.

## Lưu ý
- Đừng tin bảng public như chân lý — nó chỉ là prior. Eval của bạn mới quyết.
- Kiểm tra tab Activity của OpenRouter để biết request chạy đúng provider/giá như kỳ vọng.
