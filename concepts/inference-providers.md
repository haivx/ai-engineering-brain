# Inference provider: tốc độ đổi lấy giá

## Tách bạch hai thứ
- **Model** quyết định CHẤT LƯỢNG câu trả lời.
- **Provider** (bên chạy inference) quyết định bạn nhận được nó NHANH hay CHẬM, và với GIÁ nào.
Cùng một open model có thể chạy trên nhiều provider với chất lượng gần như y hệt nhưng giá & tốc độ chênh lệch rất lớn.

## Đánh đổi cốt lõi
- Provider tốc độ cao (ví dụ chip chuyên dụng cho inference, throughput hàng nghìn token/s) → NHANH nhưng ĐẮT HƠN.
- Provider phổ thông → RẺ hơn nhiều nhưng chậm hơn.
Chọn nhanh khi: UX realtime, agent loop nhiều bước, demo cần cảm giác mượt.
Chọn rẻ khi: việc chạy theo lô không gấp, học tập/thử nghiệm.

## LiteLLM + OpenRouter (stack hiện tại)
- **LiteLLM**: một lớp wrapper thống nhất — gọi mọi provider qua cùng một hàm `completion()` kiểu OpenAI.
  Đổi model = đổi một chuỗi string.
- **OpenRouter**: một router chỉ cần một API key để truy cập nhiều model/provider. Trả trước bằng credit,
  trừ dần âm thầm theo token (không hiện màn hình xác nhận thanh toán ở mỗi lần gọi).
- Ép dùng một provider cụ thể: truyền `{"provider": {"order": ["<name>"]}}` qua `extra_body`.
  Thêm `"allow_fallbacks": false` nếu muốn ghim cứng, không cho fallback sang host khác.
- Lưu ý: nếu provider được chỉ định đang quá tải, OpenRouter sẽ tự fallback → kiểm tra tab Activity
  để biết request THỰC SỰ chạy trên host nào (giá/host hiển thị ở đó).

## An toàn chi phí
Cách đốt tiền nhanh nhất: một agent kẹt trong retry loop chạy hàng nghìn lần.
→ Đặt giới hạn chi tiêu trên dashboard NGAY từ đầu.
