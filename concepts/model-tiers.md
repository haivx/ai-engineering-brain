# Ba tầng model (bản chi tiết)

Xem thêm concepts/routing.md — đây là bảng phân loại để quyết định escalate.

| Tầng | Dùng cho | Đặc điểm |
|---|---|---|
| Frontier đóng | ~20% task khó nhất: kiến trúc phức tạp, debug hiểm, agent loop dài | Đắt, mạnh nhất, khó thay thế |
| Rẻ-mà-tốt | Daily driver: phần lớn coding thường ngày | Cân bằng giá/chất |
| Open rẻ / self-host | Boilerplate, extraction, phân loại, format, test | Rẻ như cho, đủ dùng cho việc dễ |

## Quy tắc quyết định
1. Task này thuộc tầng nào? (theo độ khó thật, không theo cảm giác)
2. Model rẻ nhất của tầng đó đã ĐO đạt chưa? (eval set)
3. Nếu chưa chắc → thử tầng rẻ trước, có eval bắt lỗi thì escalate.

## Khi "hết token dùng tạm"
- Việc lặt vặt → tầng open rẻ.
- Coding cần chất → tầng rẻ-mà-tốt.
- Việc khó thật → ĐỪNG hạ tầng. Đợi/nạp thêm còn hơn để model rẻ làm hỏng rồi sửa.

(Tên model cụ thể xoay vòng liên tục — tra bản mới ở references/leaderboards.md.)
