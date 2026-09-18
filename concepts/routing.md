# Routing

Kỹ năng cốt lõi của AI Engineering: **dùng model rẻ cho phần dễ, và chỉ leo thang lên model đắt cho phần khó.**

## Vì sao
"Model nào tốt nhất" là câu hỏi sai. Câu hỏi đúng: "PHẦN NÀO của công việc cần model mạnh, và phần nào model rẻ cũng ổn?"
Một tác vụ thường gồm nhiều bước với độ khó khác nhau. Bắt Opus làm cả những bước tầm thường = đốt tiền vô ích.
Bắt model rẻ làm bước khó = hỏng việc và tốn công đi sửa.

## Ba tầng model (khung để phân loại tác vụ)
- **Closed frontier** (Opus, các bản GPT lớn, Gemini Pro): dành cho ~20% tác vụ khó nhất — kiến trúc phức tạp,
  debug hóc búa, agent loop dài.
- **Cheap-but-good** (Sonnet, DeepSeek Flash...): ngựa thồ hằng ngày, phần lớn công việc thường nhật.
- **Open-weight giá rẻ / self-hosted**: việc vặt, boilerplate, extraction, định dạng.
  (Tên model chỉ là ví dụ — chúng thay đổi liên tục. Xem references/leaderboards.md để tra tên hiện hành.)

## Điều kiện tiên quyết
Muốn route đúng, bạn phải biết "model rẻ đủ tốt cho giai đoạn nào" → bạn phải ĐO → bạn cần một bộ eval.
Xem concepts/eval.md. Không có eval thì routing chỉ là đoán mò.

## Cạm bẫy: compounding error
Trong một agent loop nhiều bước, một model rẻ lệch 5% ở mỗi bước → sau 10 bước là lệch hoàn toàn.
Đây là lý do reasoning nhiều bước thường phải dùng model mạnh, ngay cả khi từng bước riêng lẻ trông có vẻ đơn giản.
