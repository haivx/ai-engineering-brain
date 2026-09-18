# Chunking & Embedding

*Framing stub — chưa có experiment chống lưng. Xem danh sách cuối file.*

Retrieval không đi tìm tài liệu, nó đi tìm **chunk**. Chunk mới là đơn vị hệ thống thực sự nhìn thấy, nên cách bạn cắt tài liệu đặt ra trần chất lượng cho mọi thứ phía sau — đổi embedding model không cứu được một chiến lược cắt sai. Đây là nơi công sức bỏ ra có tỉ suất hoàn vốn cao nhất trong một pipeline RAG.

- **Đánh đổi cốt lõi, hai lỗi đối xứng**: chunk quá nhỏ → hit đúng nhưng thiếu ngữ cảnh, model trả lời sai dù retrieval đúng. Chunk quá lớn → vector bị trung bình hóa qua nhiều chủ đề, câu hỏi cụ thể không hit nổi. Chunk tốt là chunk đủ hẹp để vector "nói về một thứ", và đủ rộng để tự nó trả lời được câu hỏi.
- **Overlap là bảo hiểm cho phần biên**, không phải nút "tăng chất lượng". Nó chống việc cắt đứt một ý ngay giữa chừng. Cái giá: sinh ra nhiều chunk gần giống nhau, và chúng có thể chiếm hết các suất trong top-k.
- **Cắt theo cấu trúc tốt hơn cắt theo số ký tự** khi tài liệu có cấu trúc (heading, đoạn, hàm, mục). Fixed-size chỉ nên là phương án dự phòng cho văn bản không cấu trúc.
- **Metadata đi kèm chunk** (nguồn, tiêu đề, vị trí, ngày) thường cải thiện kết quả nhiều hơn việc tinh chỉnh chunk size: nó cho phép lọc trước khi tìm, và cho phép trích dẫn nguồn trong câu trả lời.
- **Chunk size và overlap là tham số cần ĐO, không phải chọn theo cảm giác.** Đổi đúng một biến, chạy lại recall@k trên cùng bộ câu hỏi — đúng kỷ luật so sánh trước/sau trong `playbooks/build-eval-set.md`.
- **Bất đối xứng query–document**: câu hỏi thì ngắn, chunk thì dài. Đây là lý do một số embedding model có prefix/instruction riêng cho query và cho document — dùng sai chiều làm giảm chất lượng một cách âm thầm.
- **Re-embed là thao tác toàn tập**: đổi chiến lược chunk hoặc đổi model nghĩa là index lại toàn bộ. Hãy lưu cấu hình chunk + tên model *cùng với* index, nếu không sau vài tuần bạn sẽ không biết index hiện tại được sinh ra như thế nào.

**Khi nào KHÔNG cần cái này:** khi phải tự train hoặc fine-tune embedding model, tự cài đặt ANN index, hay tối ưu quantization/sharding vector — hãy dùng model và vector DB có sẵn, dồn toàn bộ công sức vào chiến lược cắt và vào việc đo.

## Cần làm `experiments/data-engineering/chunking/`
- Quét lưới chunk size × overlap trên cùng bộ câu hỏi, đo recall@k cho từng cấu hình.
- So cắt theo heading với cắt fixed-size trên chính repo này (tài liệu có cấu trúc rõ).
- Đo tỉ lệ suất trong top-k bị chiếm bởi các chunk gần trùng nhau do overlap sinh ra.
