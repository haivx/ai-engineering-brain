# Golden Dataset (eval set cho RAG / agent)

*Framing stub — chưa có experiment chống lưng. Xem danh sách cuối file.*

Không có một bộ câu hỏi kèm đáp án chuẩn, mọi thay đổi trong pipeline RAG hay agent đều chỉ được đánh giá bằng cảm giác — và cảm giác thì luôn nói rằng thay đổi vừa rồi có ích. Golden dataset là thứ biến "tôi thấy nó tốt hơn" thành một con số so sánh được giữa hai lần chạy. Phương pháp luận eval tổng quát nằm ở `concepts/eval.md`; file này chỉ nói về phần đặc thù của RAG/agent.

- **Tách hai tầng eval, tuyệt đối không gộp**: eval *retrieval* (chunk đúng có nằm trong top-k không — recall@k, MRR) và eval *generation* (câu trả lời có bám vào chunk lấy được không — groundedness, tỉ lệ bịa). Gộp thành một điểm thì khi điểm tụt bạn không biết phải sửa retriever hay sửa prompt.
- **Điểm generation chỉ có nghĩa khi retrieval đã đúng.** Luôn đọc hai con số cạnh nhau: generation tệ trên một retrieval sai không nói gì về chất lượng model.
- **Cách tạo case rẻ nhất: đi ngược từ tài liệu ra câu hỏi.** Mở một chunk, tự hỏi "câu hỏi nào mà đoạn này là đáp án duy nhất", ghi lại `chunk_id` làm ground truth. Cách này cho bạn ground truth cho phần retrieval hoàn toàn miễn phí.
- **Bổ sung case từ câu hỏi thật của người dùng.** Câu hỏi tự chế thường quá sạch và quá đúng từ khóa; câu hỏi thật mới là phân bố bạn cần đo.
- **Bắt buộc phải có nhóm "không trả lời được"**: những câu hỏi mà corpus không hề chứa đáp án. Thiếu nhóm này thì bạn không bao giờ đo được xu hướng bịa — hệ thống luôn trả lời một cái gì đó và luôn trông có vẻ ổn.
- **LLM sinh nháp được, nhưng đáp án chuẩn phải do người duyệt.** Một golden set do LLM tự sinh rồi tự chấm là một vòng lặp khép kín, nó đo sự nhất quán của model chứ không đo tính đúng.
- **Đóng băng và đánh version.** Sửa case là làm mất giá trị so sánh của mọi con số cũ; hãy tạo version mới và ghi rõ đã đổi gì, thay vì chỉnh tại chỗ.
- **Vài chục case có chủ đích, phủ đủ các nhóm, giá trị hơn hàng nghìn case ngẫu nhiên** — cùng lập luận với `playbooks/build-eval-set.md`, và mỗi case cần log có cấu trúc để truy ngược (`concepts/agent-infra/observability.md`).

**Khi nào KHÔNG cần cái này:** khi cần benchmark công khai để so với thế giới, khi vận hành một đội annotator với công cụ labeling và đo inter-annotator agreement — ở quy mô một người, 30–100 case tự duyệt kèm version hóa bằng git là đủ.

## Cần làm `experiments/data-engineering/golden-dataset/`
- Dựng một golden set ~30 case từ chính repo này, mỗi case gắn `chunk_id` ground truth.
- Đo recall@k và groundedness **tách rời**, chứng minh một thay đổi cải thiện cái này nhưng làm hỏng cái kia.
- Chứng minh nhóm "không trả lời được" bắt được hành vi bịa mà các nhóm còn lại không thấy.
