# NOTES.md — memory/ (session state xuyên nhiều lần chạy vs. log durable)

- "Session" ở đây được định nghĩa thuần túy theo vận hành — một chuỗi các lần
  gọi liên tiếp của cùng một script dùng chung một `session.json` — hoàn toàn
  không dính tới đồng hồ hệ thống. Session id được suy ra bằng cách đếm các
  sự kiện `session_start` đã có trong log durable, và hóa ra đó là một cách
  gọn gàng để có session id deterministic, tăng đơn điệu, mà không cần
  timestamp hay một file đếm.
- Bước promotion (`session_summary` được ghi thêm *trước khi* `session.json`
  bị xóa) mới là phần thực sự quan trọng, hơn cả bản thân việc hết hạn. Xóa
  session state mà không promote trước thì chỉ là lặp lại đúng kiểu thất bại
  crash-rồi-xóa-sạch của `state/`, ở cao hơn một tầng (phạm vi session thay vì
  phạm vi một lần chạy) — bản thân việc hết hạn không phải phần an toàn,
  promotion mới là.
- Thứ tự có ý nghĩa thật trong code: ghi bản tóm tắt vào log, xác nhận lần ghi
  đó, rồi mới xóa `session.json`. Nếu đảo ngược hai thao tác ấy (hoặc không
  sắp thứ tự rõ ràng), một cú crash xen giữa chúng sẽ tạo ra đúng sự mất mát
  dữ liệu mà việc tách tầng này sinh ra để ngăn chặn — chạy thật khiến sự phụ
  thuộc thứ tự đó trở nên cụ thể thay vì lý thuyết suông.
- Bất ngờ: chẳng có gì trong chuyện "session vs. log durable" đòi hỏi một cơ
  chế lưu trữ khác (cả hai vẫn chỉ là file thường) — khác biệt nằm hoàn toàn ở
  chỗ mỗi file được phép chịu điều gì: `session.json` là thứ dùng-rồi-bỏ theo
  thiết kế và bị xóa thẳng; `log.jsonl` không bao giờ bị xóa, chỉ được ghi
  thêm. Tuổi thọ là một chính sách do code áp đặt, không phải một thuộc tính
  của tầng lưu trữ.
- Việc lần chạy #3 rơi vào một session id mới tinh (S2) thay vì tiếp tục S1 là
  hành vi đúng, nhưng đáng đánh dấu như một quyết định thiết kế thật: script
  này coi "session hết hạn" nghĩa là "làm lại từ đầu, không có tính liên tục",
  chứ không phải "làm lại từ đầu với bản tóm tắt của S1 được nạp lại". Một hệ
  thống muốn có tính liên tục sẽ phải đọc tường minh `session_summary` gần nhất
  ra khỏi log khi bootstrap một session mới — đó là lựa chọn có chủ đích mà bài
  tập này KHÔNG làm, và KHÔNG phải hệ quả tự động của bản thân pattern phân tầng.
- `SESSION_MAX_RUNS = 2` là một ngưỡng nhỏ, tùy ý, chọn chỉ để việc hết hạn lộ
  ra trong 3 lần chạy cho bản chứng minh này. Không có gì khác trong thiết kế
  phụ thuộc vào con số cụ thể đó; một hệ thống thật sẽ gắn việc hết hạn với thứ
  gì đó có ý nghĩa (thời gian nhàn rỗi, hạn mức token, một lệnh đóng tường minh)
  thay vì một số lần chạy cố định.
- Điều này KHÔNG chứng minh: nó không kiểm thử các lần chạy đồng thời trên cùng
  session (hai tiến trình tranh chấp `session.json`), và không minh họa việc đọc
  ngược các dữ kiện RA KHỎI một `session_summary` cũ để dùng cho session mới —
  chỉ chứng minh rằng bản tóm tắt được ghi lại an toàn vào log khi session chết.
