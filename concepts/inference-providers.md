# Inference providers: tốc độ vs giá

## Tách bạch hai thứ
- **Model** quyết định CHẤT LƯỢNG câu trả lời.
- **Provider** (nhà chạy inference) quyết định bạn nhận nó NHANH hay CHẬM, và GIÁ bao nhiêu.
Cùng một model open có thể chạy trên nhiều provider, chất lượng gần như y hệt, giá & tốc độ chênh lớn.

## Đánh đổi cốt lõi
- Provider tốc độ cao (vd chip chuyên inference, throughput ngàn token/s) → NHANH nhưng ĐẮT hơn.
- Provider phổ thông → RẺ hơn nhiều nhưng chậm hơn.
Chọn nhanh khi: realtime UX, agent loop nhiều bước, demo cần mượt.
Chọn rẻ khi: batch không gấp, học/thử nghiệm.

## LiteLLM + OpenRouter (stack hiện dùng)
- **LiteLLM**: wrapper thống nhất, gọi mọi provider bằng cùng hàm `completion()` kiểu OpenAI.
  Đổi model = đổi một string.
- **OpenRouter**: router một-API-key truy cập nhiều model/provider. Trả trước bằng credit,
  trừ ngầm theo token (không có màn xác nhận thanh toán mỗi lần gọi).
- Ép provider cụ thể: nhét `{"provider": {"order": ["<tên>"]}}` qua `extra_body`.
  Thêm `"allow_fallbacks": false` nếu muốn ép cứng, không cho rớt sang nhà khác.
- Lưu ý: nếu provider chỉ định hết chỗ, OpenRouter tự fallback → kiểm tra tab Activity
  xem request THẬT SỰ chạy nhà nào (giá/nhà hiển thị ở đó).

## An toàn chi phí
Rủi ro đốt tiền nhanh nhất: agent kẹt vòng lặp retry chạy hàng nghìn lần.
→ Đặt spending limit trên dashboard NGAY từ đầu.
