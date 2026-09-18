# Data Quality Checks

*Framing stub — chưa có experiment chống lưng. Xem danh sách cuối file.*

Lỗi dữ liệu nguy hiểm nhất không làm crash. Pipeline chạy tới cuối, in ra một con số, và con số đó sai — không có exception, không có stack trace, không có gì để grep. Lớp kiểm tra chất lượng tồn tại vì đúng một lý do: biến những lỗi âm thầm đó thành lỗi ồn ào, càng gần nguồn dữ liệu càng tốt.

- **Dedup: thứ cần bắt là near-duplicate, không phải trùng tuyệt đối.** Hai hậu quả khác nhau — trong retrieval, các bản gần trùng chiếm hết suất top-k; trong eval, một bản sao nằm ở cả hai phía train/eval thổi phồng điểm. Dedup **trước** khi chia tập.
- **Validate theo schema ngay tại biên nhập dữ liệu**: kiểu, trường bắt buộc, khoảng giá trị hợp lệ. Kiểm lúc nạp, không phải lúc dùng — lỗi càng gần nguồn thì càng rẻ để tìm ra.
- **Đếm là phép kiểm rẻ nhất và bị bỏ qua nhiều nhất**: số dòng vào/ra ở mỗi bước, số NaN, số chuỗi rỗng, độ dài chunk min/max. Một bước lọc âm thầm vứt đi 40% dữ liệu trông y hệt một bước lọc chạy đúng.
- **Drift**: phân bố dữ liệu hôm nay lệch dần khỏi lúc bạn dựng eval set, nên eval cũ dần đo sai thứ. Dấu hiệu rẻ tiền: độ dài trung bình, tỉ lệ theo nguồn/nhãn, tỉ lệ ngôn ngữ hoặc ký tự lạ. Không cần công cụ — lưu snapshot vài thống kê rồi so định kỳ.
- **Danh sách lỗi âm thầm hay gặp**: encoding hỏng (mojibake), ký tự vô hình và whitespace khiến dedup trượt, ô rỗng biến thành chuỗi `"None"`/`"nan"`, lệch timezone, join làm phình dòng, và truncation âm thầm khi vượt giới hạn độ dài trường hay context.
- **Mỗi giả định về dữ liệu nên có một assertion tương ứng.** "Cột này luôn unique", "độ dài luôn > 0", "tổng số dòng không đổi sau bước này" — một assertion fail ồn ào rẻ hơn rất nhiều so với một báo cáo sai.
- **Kiểm tra phải chạy tự động cùng pipeline và ghi log có cấu trúc**, không phải làm tay một lần rồi quên. Không có trace per-step thì bạn phát hiện được có lỗi nhưng không debug được (`concepts/agent-infra/observability.md`).

**Khi nào KHÔNG cần cái này:** khi phải thương lượng data contract giữa nhiều team, dựng monitoring drift thời gian thực, hay xây lineage/data catalog — ở quy mô một người, một script check chạy cùng pipeline với vài assertion và một snapshot thống kê là đủ.

## Cần làm `experiments/data-engineering/data-quality/`
- Đo tỉ lệ near-duplicate trong corpus và ảnh hưởng trực tiếp của nó lên thành phần top-k.
- Tiêm một lỗi âm thầm (mojibake hoặc join phình dòng), chứng minh pipeline vẫn "chạy xong" và assertion là thứ duy nhất bắt được.
- Lưu snapshot thống kê ở hai thời điểm và dựng một phép so drift tối giản trên đó.
