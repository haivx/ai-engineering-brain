# Playbook: chọn một model giá rẻ để chữa cháy

Dùng khi bạn hết quota/token và cần một model thay thế gấp.

## Các bước
1. Mở **llm-stats.com**, lọc theo trục bạn cần (coding / rẻ nhất / open-weight).
2. Đối chiếu giá THẬT trên **openrouter.ai** (giá đổi liên tục — luôn kiểm tra lại ở đây).
3. Phân loại tác vụ đang làm (xem concepts/model-tiers.md):
   - Việc vặt / boilerplate / extraction → chọn open model rẻ nhất mà vẫn "dùng được".
   - Coding cần chất lượng → một open coding model tử tế với context đủ dài.
   - Việc thực sự khó → cân nhắc ĐỪNG hạ cấp (chờ / nạp thêm tiền thì hơn).
4. Trong LiteLLM: chỉ đổi chuỗi `MODEL`. Không đổi gì khác.
5. Nếu công việc quan trọng → cho chạy qua bộ eval (playbooks/build-eval-set.md) trước khi tin nó.

## Ghi chú
- Đừng coi các bảng xếp hạng công khai là chân lý — chúng chỉ là một prior. Eval của bạn mới là thứ quyết định.
- Kiểm tra tab Activity của OpenRouter để xác nhận request đã chạy đúng provider/giá bạn mong đợi.
