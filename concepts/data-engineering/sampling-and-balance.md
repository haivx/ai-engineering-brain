# Sampling & Balance

*Framing stub — chưa có experiment chống lưng. Xem danh sách cuối file.*

Tập dữ liệu bạn đang có hiếm khi trùng với phân bố bạn muốn *đo*, và cũng hiếm khi trùng với phân bố bạn muốn *dạy*. Sampling là cách nói rõ ra mình đang làm việc trên phân bố nào — bỏ qua bước này thì một con số như "pass rate 82%" không cho biết nó là 82% của cái gì.

- **Tách hai mục đích, đừng gộp**: lấy mẫu để ĐO (eval) và lấy mẫu để DẠY (train) có mục tiêu ngược nhau. Eval nên phản ánh phân bố thật, hoặc báo cáo tách theo từng nhóm; train thì có thể cân bằng lại một cách có chủ đích.
- **Stratified sampling** — chia theo nhóm trước, rồi lấy mẫu trong từng nhóm. Dùng khi eval set nhỏ (vài chục case): lấy mẫu ngẫu nhiên thuần ở cỡ đó hoàn toàn có thể bỏ sót trọn một nhóm mà bạn không nhận ra.
- **Weighted sampling** — mỗi dòng một trọng số, dùng để oversample lớp hiếm hoặc nguồn dữ liệu quan trọng. Nhớ rằng trọng số làm lệch luôn cả metric: nếu lấy mẫu có trọng số mà báo cáo như mẫu đều, con số đó sai.
- **Imbalanced dataset** — accuracy trở nên vô nghĩa khi 95% dữ liệu thuộc một lớp. Hãy nhìn recall/precision theo từng lớp, hoặc pass rate tách theo nhóm, thay vì một con số tổng.
- **Leakage là cạm bẫy nghiêm trọng nhất**, không phải mất cân bằng. Chia train/eval theo **document/source**, không theo chunk: cùng một tài liệu bị cắt thành nhiều chunk rơi vào cả hai bên sẽ đẩy điểm lên một cách giả tạo. Dedup trước, chia sau.
- **Ghi lại seed và quy tắc lấy mẫu.** Một eval set không tái lập được thì mọi so sánh trước/sau đều vô nghĩa — cùng lý do với ranh giới determinism trong `concepts/agent-infra/determinism.md`.
- **Đọc con số theo cỡ mẫu**: một nhóm có 3 case thì chênh 1 case đã là 33%. Đừng diễn giải dao động ở nhóm nhỏ như một tín hiệu thật.

**Khi nào KHÔNG cần cái này:** khi phải dùng SMOTE và các kỹ thuật tái cân bằng nâng cao, class weight trong hàm loss, hay sampling phân tán trên cụm máy — với một eval set thủ công vài chục tới vài trăm case, stratify bằng tay cộng ghi lại seed là đủ.

## Cần làm `experiments/data-engineering/sampling/`
- Dựng cùng một eval set theo hai cách (random thuần vs stratified) và so độ phủ nhóm ở cỡ mẫu nhỏ.
- Chứng minh leakage: chia theo chunk thay vì theo document, đo recall bị thổi lên bao nhiêu.
- Đổi seed nhiều lần trên cùng quy tắc lấy mẫu, đo dao động pass rate để biết ngưỡng nhiễu của bộ eval.
