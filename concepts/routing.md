# Routing

Kỹ năng lõi của AI Engineering: **dùng model rẻ cho phần dễ, chỉ escalate lên model đắt ở phần khó.**

## Vì sao
"Model nào tốt nhất" là câu hỏi sai. Câu đúng: "phần việc NÀO cần model mạnh, phần nào model rẻ là đủ?"
Một task thường gồm nhiều bước độ khó khác nhau. Bắt Opus làm cả những bước tầm thường = đốt tiền vô ích.
Bắt model rẻ làm bước khó = hỏng việc, tốn công sửa.

## Ba tầng model (khung để phân loại task)
- **Frontier đóng** (Opus, GPT lớn, Gemini Pro): cho ~20% task khó nhất — kiến trúc phức tạp,
  debug hiểm, agent loop dài.
- **Rẻ-mà-tốt** (Sonnet, DeepSeek Flash...): daily driver, phần lớn việc thường ngày.
- **Open-weight rẻ / self-host**: việc lặt vặt, boilerplate, extraction, format.
  (Tên model chỉ là ví dụ — chúng xoay vòng liên tục. Xem references/leaderboards.md để tra bản mới.)

## Điều kiện tiên quyết
Muốn route đúng thì phải biết "model rẻ đủ tốt cho khâu nào" → phải ĐO → phải có eval set.
Xem concepts/eval.md. Không có eval thì routing chỉ là đoán mò.

## Cạm bẫy: sai số cộng dồn
Trong agent loop nhiều bước, model rẻ lệch 5% mỗi bước → qua 10 bước lệch hẳn.
Đây là lý do reasoning nhiều bước thường phải dùng model mạnh, dù từng bước nhìn có vẻ đơn giản.
