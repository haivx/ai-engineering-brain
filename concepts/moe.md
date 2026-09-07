# MoE & vì sao model open rẻ

## MoE (Mixture-of-Experts)
Model có tổng N tham số nhưng mỗi lần forward pass chỉ *activate* một phần nhỏ.
Ví dụ dạng "117B tổng, ~5B active/token": chạy nhẹ như model ~5B dù kiến thức của model lớn.
→ inference rẻ và nhanh hơn nhiều so với model dense cùng cỡ.

## Vì sao gọi API model open-weight lại rẻ đến vậy
1. **Open-weight** = không có phí bản quyền, chỉ trả tiền hạ tầng (điện/GPU).
2. **MoE** = ít tham số active → tốn ít compute mỗi token.
3. Nhiều provider cạnh tranh host cùng một model → giá bị ép xuống.

Kết quả: nhiều model open đủ tốt cho việc hằng ngày mà giá chỉ bằng vài % model đóng.
