# Tabular Ops (numpy / pandas)

*Framing stub — chưa có experiment chống lưng. Xem danh sách cuối file.*

Dữ liệu cho RAG, eval set và fine-tune nhẹ gần như luôn đến dưới dạng bảng: jsonl, csv, parquet — một dòng một chunk, một case, một mẫu. Vấn đề cần giải không phải "chạy cho nhanh" mà là **giảm số chỗ có thể sai âm thầm**: một vòng lặp Python trên từng dòng vừa chậm vừa dài, và code càng dài thì lỗi lọc nhầm, gán nhầm, mất dòng càng dễ lẩn. Mental model cốt lõi: nghĩ theo **cột** và theo **mask**, không nghĩ theo dòng.

- **Vectorized ops** — coi mỗi cột là một mảng, phép toán áp lên cả cột một lần. Dùng mặc định cho mọi phép biến đổi trên toàn bảng; chỉ rơi về vòng lặp khi thao tác thật sự không biểu diễn được theo cột (gọi API cho từng dòng chẳng hạn).
- **Broadcasting** — hai mảng khác shape vẫn tính được với nhau theo quy tắc mở rộng chiều. Dùng khi so một vector với cả một ma trận (một query embedding vs N chunk embedding). Cạm bẫy: broadcast *thành công* ngoài ý muốn → ra shape sai mà không hề báo lỗi. Luôn assert shape kết quả.
- **Boolean mask** — điều kiện lọc là dữ liệu hạng nhất: tạo mảng True/False, ghép bằng `&`, `|`, `~`, rồi mới index. Lợi ích thật là mask **đếm được**: đếm số dòng khớp trước khi lọc, để biết mình sắp giữ lại bao nhiêu.
- **groupby = split–apply–combine** — dùng khi cần thống kê theo nhãn/nguồn/loại. Đây chính là thao tác kiểm tra phân bố của một eval set hay một corpus.
- **merge / join** — luôn đếm số dòng trước và sau. Join trên khóa không unique làm **phình số dòng âm thầm**; đây là lỗi hay gặp nhất khi ghép metadata vào chunk, và nó không crash.
- **NaN** — NaN không bằng chính nó; phép toán số học lan NaN ra ngoài; nhưng nhiều hàm gộp lại *âm thầm bỏ qua* NaN, nên một giá trị trung bình có thể đang tính trên ít dòng hơn bạn tưởng. Hãy quyết định tường minh: fill, drop, hay giữ và ghi nhận — đừng để mặc định quyết hộ.
- **copy vs view** — gán giá trị lên một slice có thể không ăn vào bảng gốc. Khi thấy cảnh báo kiểu `SettingWithCopy`, đó là tín hiệu bạn đang sửa một bản sao, không phải dữ liệu thật.

**Khi nào KHÔNG cần cái này:** khi dữ liệu vượt RAM (Spark/Dask/out-of-core), khi phải tối ưu dtype/bộ nhớ ở quy mô lớn, hoặc khi mô hình hóa data warehouse — ở quy mô eval set và corpus RAG cá nhân (hàng nghìn tới hàng trăm nghìn dòng), pandas trên một máy là đủ và mọi thứ ngoài đó là phạm vi Data Engineer chuyên nghiệp.

## Cần làm `experiments/data-engineering/tabular-ops/`
- So vòng lặp từng dòng vs vectorized trên chính corpus của mình: thời gian + số dòng code.
- Ép một join sai khóa và chứng minh số dòng phình lên mà không có lỗi nào được ném ra.
- Chứng minh NaN âm thầm đổi kết quả của một phép gộp (mean tính trên mẫu nhỏ hơn dự kiến).
