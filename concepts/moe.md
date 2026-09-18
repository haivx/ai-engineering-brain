# MoE & vì sao các open model giá rẻ lại rẻ đến vậy

## MoE (Mixture-of-Experts)
Model có tổng cộng N tham số, nhưng mỗi lượt forward chỉ *kích hoạt* một phần nhỏ trong số đó.
Ví dụ dạng "117B tổng, ~5B active/token": nó chạy nhẹ như một model ~5B trong khi vẫn giữ lượng kiến thức của một model lớn.
→ inference rẻ và nhanh hơn nhiều so với một dense model cùng kích cỡ.

## Vì sao gọi API của một open-weight model lại rẻ như vậy
1. **Open-weight** = không mất phí bản quyền, bạn chỉ trả tiền hạ tầng (điện/GPU).
2. **MoE** = ít tham số được kích hoạt → ít phép tính hơn trên mỗi token.
3. Nhiều nhà cung cấp cùng cạnh tranh host một model → giá bị đẩy xuống.

Kết quả: nhiều open model đủ tốt cho công việc hằng ngày với chi phí chỉ bằng vài phần trăm một model closed.
