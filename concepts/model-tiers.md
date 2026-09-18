# Ba tầng model (bản chi tiết)

Xem thêm concepts/routing.md — đây là bảng phân loại để quyết định khi nào nên leo thang (escalate).

| Tầng | Dùng cho | Đặc điểm |
|---|---|---|
| Closed frontier | ~20% việc khó nhất: kiến trúc phức tạp, debug hóc búa, agent loop dài | Đắt, mạnh nhất, khó thay thế |
| Cheap-but-good | Ngựa thồ hằng ngày: phần lớn việc coding thường nhật | Cân bằng giá/chất lượng |
| Open giá rẻ / self-hosted | Boilerplate, extraction, classification, định dạng, viết test | Cực rẻ, đủ tốt cho việc dễ |

## Quy tắc ra quyết định
1. Tác vụ này thuộc tầng nào? (theo độ khó thật, không theo cảm tính)
2. Model rẻ nhất trong tầng đó đã được ĐO là đủ tốt chưa? (bộ eval)
3. Nếu chưa chắc → thử tầng rẻ hơn trước; leo thang khi eval bắt được lỗi.

## Khi bạn "hết token và cần chữa cháy"
- Việc vặt → tầng open giá rẻ.
- Coding cần chất lượng → tầng cheap-but-good.
- Việc thực sự khó → ĐỪNG hạ cấp. Chờ / nạp thêm tiền vẫn hơn là để model rẻ làm hỏng rồi phải đi sửa.

(Tên model cụ thể thay đổi liên tục — tra tên hiện hành trong references/leaderboards.md.)
