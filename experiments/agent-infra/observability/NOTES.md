# NOTES.md — lần chạy thực sự cho thấy điều gì

- Con số pass-rate và log có cấu trúc trả lời hai câu hỏi khác nhau, và bạn cần
  cả hai. `12/18` (66,7%) cho biết *bao nhiêu* thứ đang hỏng; grep
  `logs/run_baseline.jsonl` theo `case_id` cho biết *case nào*, *bước pipeline
  nào*, và *vì sao*, chỉ trong một lệnh. `naive_baseline_demo.py` cũng đạt đúng
  12/18 với zero cấu trúc và không trả lời được bất kỳ câu hỏi tiếp theo nào —
  xem RUN.md §5.

- Đổi đúng một biến (`--threshold` 0.0 -> 0.2) làm pass rate dịch chuyển một
  lượng thật, khác không (+11,1 điểm), và dịch chuyển qua các case bị lật kết
  quả giải thích được, không phải nhiễu. `compare_runs.py` dựng thẳng các case
  bị lật đó từ `results/eval_*.json` — không cần đọc lại log JSONL mới có phán
  quyết trước/sau, chỉ cần đọc lại khi muốn tìm *nguyên nhân gốc*.

- Thay đổi ngưỡng không phải một thắng lợi thuần túy. Nó sửa được 5 false
  positive (văn bản lạc đề tình cờ khớp một từ khóa) nhưng làm hỏng 3 true
  positive (ticket thật mà tín hiệu duy nhất chỉ là một từ khóa). Một con số
  pass-rate đơn lẻ sẽ hiện ra "+11,1%" và che giấu hoàn toàn sự đánh đổi đó;
  chính bản diff theo từng case trong `compare_runs.py` mới phơi nó ra.
  Bất ngờ: rất dễ chỉ báo cáo con số tổng rồi tuyên bố thay đổi này tốt hơn hẳn,
  trong khi nó không phải vậy.

- Phân biệt "pipeline đã chạy và cho câu trả lời sai" với "pipeline đã crash"
  đòi hỏi một trường `status` (`ok` vs `error`) ở mức bước, không chỉ ở mức
  case. Cả hai trông y hệt nhau nếu chỉ đếm pass/fail trần. Đây là trường duy
  nhất khiến lập luận về lỗi được định vị ở RUN.md §5 trở nên khả thi.

- `step_seq` cộng với tên `step` (chứ không chỉ "đã xảy ra lỗi") cho tôi thấy
  cú crash xảy ra ở `normalize`, tại bước 1 trên 5 — trước khi `tokenize`,
  `score` hay `decide` kịp chạy. Không có bản ghi theo từng bước, chữ "nó fail"
  chẳng nói gì về việc giai đoạn nào trong pipeline 4 giai đoạn thậm chí còn
  chưa khởi động.

- Thực ra không cần seeding nào để có pass rate ổn định: hệ thống này có zero
  ngẫu nhiên trong logic quyết định (chỉ đếm từ khóa thuần túy), nên hai lần
  chạy cùng một ngưỡng cho ra giá trị `pass_rate` giống nhau từng bit (đã kiểm
  chứng ở RUN.md §4). Yêu cầu "hãy seed phần bất định của bạn" hóa ra được thỏa
  mãn bằng cách không có phần bất định nào trên đường đi được chấm điểm — đáng
  ghi nhận vì một hệ thống thực tế hơn (có LLM trong vòng lặp) sẽ không được
  điều này miễn phí và sẽ cần seeding hoặc mock tường minh mới đạt cùng mức tái lập.

- `run_id` (một `uuid4`) cố ý KHÔNG được seed và khác nhau ở mỗi lần chạy. Thế
  là ổn — nó là khóa để nối dữ liệu, không phải một phần của logic được chấm
  điểm. Đó là một lời nhắc hữu ích rằng "làm cho nó deterministic" chỉ cần áp
  dụng cho những trường mà điểm eval phụ thuộc vào, không phải mọi trường trong log.

- Cắt ngắn input/output được ghi log (`_truncate`, 200 ký tự) có ý nghĩa thật
  trên thực tế: bản ghi `case_result` nhúng nguyên một dict kết quả vào trường
  `output`, và nếu không cắt ngắn thì vài case dài dòng sẽ khiến file JSONL khó
  lướt mắt hơn hẳn. Đây là mối bận tâm vận hành thật, không phải giả định — nó
  đã lộ ra trong output log thực tế (xem dấu `<truncated>` ở RUN.md §5b).

- Bộ eval harness coi "errored" là tập con nghiêm ngặt của "failed" khi chấm
  điểm (một lỗi luôn làm case đó fail) nhưng ghi log nó như một status riêng.
  Hai *tỉ lệ* thất bại khác nhau (phân loại sai vs. crash) đáng được theo dõi
  riêng, dù chỉ một con số ("passed") là chỉ số tổng — bản ghi summary giữ cả
  hai (`failed` và `errored` là hai bộ đếm riêng, không gộp).

Bằng chứng cho mọi điểm ở trên: `experiments/agent-infra/observability/`
(`router.py`, `eval_harness.py`, `compare_runs.py`, `naive_baseline_demo.py`,
`eval_cases.json`, `logs/`, `results/`, `RUN.md`).
