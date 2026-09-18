# References: công cụ data engineering & khi nào cần tra

> TUYỆT ĐỐI không ghi version, giá, hay số liệu benchmark vào đây — chúng lỗi thời rất nhanh.
> Chỉ ghi TÊN CÔNG CỤ, MỤC ĐÍCH, và KHI NÀO CẦN TRA.

## Xử lý bảng
- **NumPy** — mảng n chiều, broadcasting, boolean mask. Tra khi: cần hiểu quy tắc broadcasting hoặc thao tác trên embedding matrix.
- **pandas** — DataFrame, `groupby`, `merge`, xử lý NaN. Tra khi: quên cú pháp một phép biến đổi cụ thể, hoặc cần hiểu copy-vs-view.
- **Polars** — thay thế pandas khi dữ liệu lớn hoặc pandas chậm/chật RAM. Tra khi: pandas bắt đầu là nút cổ chai, không phải trước đó.
- **PyArrow / Parquet** — định dạng lưu theo cột. Tra khi: cần lưu corpus/eval set ở dạng đọc nhanh và giữ được kiểu dữ liệu.

## Kiểm tra chất lượng
- **Great Expectations** — bộ "expectation" khai báo được + báo cáo. Tra khi: muốn một lớp kiểm tra có cấu trúc thay vì assert rải rác.
- **Pandera** — khai báo schema cho DataFrame, nhẹ hơn Great Expectations. Tra khi: chỉ cần validate kiểu/khoảng giá trị ở mức vừa phải.
- **Pydantic** — validate từng bản ghi JSON tại biên nhập. Tra khi: xử lý structured output của LLM hoặc file jsonl.

## Chunking & embedding
- **LangChain text splitters / LlamaIndex node parsers** — đọc để lấy ý tưởng về các chiến lược cắt, kể cả khi không dùng framework đó.
- **Tokenizer của chính model đang dùng** — đếm token thật thay vì đếm ký tự. Tra khi: cần giới hạn chunk theo token hoặc ước lượng chi phí.
- **Sentence Transformers** — thư viện embedding chạy local. Tra khi: cần biết cách dùng prefix/instruction cho query vs document.
- **MTEB leaderboard** — bảng xếp hạng embedding model. Chỉ tra ĐÚNG LÚC cần chọn model; đừng chép kết quả vào repo (cùng nguyên tắc với `references/leaderboards.md`).

## Vector store
- **FAISS** — thư viện index chạy local, không có server. Tra khi: cần prototype retrieval nhanh trên một máy.
- **Chroma / Qdrant / pgvector** — có server, hoặc nhúng thẳng vào Postgres. Tra khi: cần lọc theo metadata, cần persistence, hoặc đã có sẵn Postgres.
- Với mọi vector store, ba thứ luôn phải tra: **metric** đang dùng (cosine / dot / L2), **cách filter theo metadata**, và **cách reindex** khi đổi chunking hoặc đổi embedding model.

## Metric & eval cho retrieval
- **ragas** — bộ metric sẵn cho RAG (groundedness, context precision/recall). Tra khi: muốn mượn định nghĩa metric thay vì tự chế.
- **Định nghĩa recall@k / MRR / nDCG kiểu TREC** — tra khi cần chốt chính xác công thức trước khi tự cài đặt.

## Dedup
- **datasketch** (MinHash / LSH) — tìm near-duplicate ở quy mô lớn. Tra khi: so từng cặp trở nên quá chậm.
- **rapidfuzz** — so chuỗi gần đúng. Tra khi: corpus nhỏ và chỉ cần một ngưỡng tương đồng đơn giản.

## Cách tra cứu (quy trình, không phải kết quả)
- Luôn đọc docs chính chủ theo **đúng version đang cài**, không đọc blog post cũ.
- Đọc trang "concepts"/"user guide" trước trang reference API — bạn cần mô hình tư duy, cú pháp thì tra sau.
- Với bất kỳ bảng xếp hạng nào (embedding model, vector DB benchmark): chỉ mở lúc cần ra quyết định, và không chép con số về đây.
