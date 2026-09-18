# References: leaderboards & cách tra cứu

> TUYỆT ĐỐI không chép số liệu/giá vào đây — chúng lỗi thời rất nhanh. Chỉ lưu LINK + QUY TRÌNH TRA CỨU.

## Nguồn chính
- **Artificial Analysis** — https://artificialanalysis.ai/
  Bảng tổng hợp đáng tin nhất: intelligence, coding, agentic + tốc độ & giá theo từng provider.
  Nhiều bảng khác lấy dữ liệu từ đây.
- **OpenRouter Rankings** — https://openrouter.ai/rankings
  Xếp hạng theo lượng token mà lập trình viên THỰC SỰ dùng ("thị trường bỏ phiếu"). Có kèm giá theo provider.
- **LLM-Stats** — https://llm-stats.com/leaderboards/llm-leaderboard
  Lọc theo trục: coding / rẻ nhất / open-weight / tốc độ. Tiện để chọn một model giá rẻ.
- **LMArena** — https://lmarena.ai/
  Bình chọn mù bởi con người (Elo). Bổ sung cho benchmark, nhưng thiên vị câu trả lời dài/đẹp.

## Cách tra cứu (quy trình, không phải kết quả)
- Cần model rẻ nhất mà vẫn đủ tốt → lọc "cheapest" trên LLM-Stats → kiểm tra lại giá thật trên OpenRouter.
- Cần model coding tốt nhất → xem cột coding/agentic trên Artificial Analysis.
- Đừng tin một bảng duy nhất; mỗi bảng đo một trục khác nhau. Hãy đối chiếu hai nguồn.
- Mọi con số đều phải được kiểm tra ĐÚNG LÚC bạn cần — đừng học thuộc, đừng hardcode.
