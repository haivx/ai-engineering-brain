# NOTES.md — lần chạy thực sự cho thấy điều gì

- **Một checkpoint chỉ chứng minh được một bước đã "xong" khi output của nó đã
  được commit atomic.** `pipeline.py` không bao giờ ghi thêm tên một bước vào
  `checkpoint.json` cho tới khi `os.replace()` của bước đó thành công. Điều này
  nghĩa là checkpoint và artifact trên đĩa mà nó mô tả không bao giờ mâu thuẫn
  nhau — không tồn tại khoảng thời gian nào mà checkpoint nói "transform xong"
  trong khi `step3_transformed.json` thật lại thiếu hoặc dở dang.

- **Câu trả lời thật cho "chuyện gì xảy ra với một bước làm dở" là: chẳng gì
  xảy ra với nó cả, vì nó chưa từng chạm vào đường dẫn thật.** `step_transform`
  ghi vào `step3_transformed.json.tmp.<pid>` và chỉ rename vào đúng chỗ ở cuối.
  Một `SIGKILL` rơi vào khoảng giữa (đúng thứ run.sh làm — xem RUN.md mục 2) chỉ
  để lại một file tạm mồ côi và không gì khác. Bước đó có thể chạy lại từ đầu an
  toàn khi khởi động lại, vì nó là hàm thuần của input đã được commit
  (`step2_validated.json`) mà cú crash chưa từng đụng tới.

- **Idempotent-bằng-cách-tính-lại hóa ra đơn giản hơn mọi kiểu logic "resume
  giữa bước".** Tôi không cần theo dõi tiến độ dở dang bên trong một bước (ví dụ
  "phần tử mảng nào đã được transform") — các bước rẻ cứ luôn bắt đầu lại từ đầu
  của chính chúng. Điều đó chỉ đúng vì mỗi bước đều nhỏ, deterministic, và đọc
  một file input ổn định; nó sẽ không dùng được nguyên xi cho một bước có side
  effect đắt đỏ hoặc không idempotent (ví dụ "gửi email", "trừ tiền thẻ") — lớp
  đó cần câu trả lời khác (dedup key, một bản ghi "tôi đã gửi cái này chưa"), và
  experiment này không phủ.

- **File tạm mồ côi thực sự vô hại, nhưng chỉ vì không ai đọc các đường dẫn
  `*.tmp.*`.** `pipeline.py` dọn chúng lúc khởi động vì gọn gàng, không phải vì
  tính đúng đắn — tôi chứng minh điều này qua dòng log "đang xóa; output thật
  chưa từng được rename thành nó, nên không gì tham chiếu tới nó". Nếu sau này
  có bước nào glob cả thư mục data thay vì đọc một đường dẫn có tên, bảo đảm này
  sẽ vỡ.

- **Việc dọn file mồ côi hóa ra là tác dụng phụ của checkpointing, không phải
  chuyện đương nhiên.** `pipeline.py` xóa các file `.tmp.*` cũ ở mỗi lần khởi
  động; `no_checkpoint_pipeline.py` không có logic đó chút nào, vì nó không có
  khái niệm "khởi động" ngoài "chạy hết mọi thứ". Một cú crash giữa `transform`
  ở bản baseline không checkpoint sẽ để file tạm mồ côi nằm trong `data/` mãi
  mãi — đã xác nhận trực tiếp (`data/step3_transformed.json.tmp.42704` trong
  lượt test đầy đủ thứ hai, xem RUN.md mục 5). Không chỉ là bản không checkpoint
  làm lại công việc; nó còn vứt rác chưa commit mà chẳng gì trong thiết kế đó
  quay lại đụng tới. Đây không phải thứ tôi định chứng minh — nó rơi ra từ việc
  dùng cùng cơ chế tiêm crash lên cả hai script.

- **Độ mịn của checkpoint là theo từng bước, không theo từng bản ghi.** Pipeline
  làm lại toàn bộ bước `transform` từ đầu thay vì tiếp tục từ chỗ nó đã tới bên
  trong bước đó. Đó là đánh đổi đúng cho một pipeline 5 bước chạy dưới một giây;
  một bước chạy lâu hơn hoặc đắt hơn sẽ cần checkpoint mịn hơn bên trong chính nó
  (hoặc nên tách bước đó thành các bước con nhỏ hơn) để khỏi làm lại việc đắt đỏ.

- **Phép đối chứng không-checkpoint làm cho cái giá trở nên cụ thể chứ không
  còn giả định.** Cùng cú crash, cùng bước, cùng 5 bước — nhưng `run4.log` cho
  thấy `fetch_input` và `validate` đều chạy lại sau khi khởi động lại, đúng phần
  việc mà bản có checkpoint đã bỏ qua tường minh (`run2.log`: hai dòng `SKIP`).
  Với 5 bước rẻ thì đó chỉ là sai số làm tròn; nhưng luận điểm tổng quát hóa rất
  tệ một khi bất kỳ bước bị bỏ qua nào chậm hoặc có side effect ra bên ngoài
  (một lời gọi API, một lần bị tính tiền) mà checkpoint lẽ ra đã ngăn không cho
  xảy ra hai lần.

- **Phép kiểm tra "lần chạy resume == lần chạy không gián đoạn" mới là bằng
  chứng mạnh nhất trong experiment này**, chứ không phải phần tường thuật log.
  `RUN.md` mục 4 cho thấy `step5_report.json` cuối cùng của cả hai lần chạy đều
  băm ra cùng một md5 (`a2d801bf...`). Một lần chạy được resume không chỉ "gần
  đủ giống" — với pipeline này (các bước thuần, deterministic) nó là artifact
  giống từng byte với thứ mà một lần chạy không hề gián đoạn sẽ tạo ra.

- **Ghi không atomic biến một thất bại khôi phục được thành một thất bại không
  khôi phục được.** `unsafe_step_demo.py` cũng bị giết y hệt, nhưng vì nó ghi
  thẳng vào đường dẫn thật thành hai mảnh, file `unsafe_output.json` kết quả là
  JSON hỏng, bị cắt cụt vĩnh viễn — và khởi động lại chẳng sửa được gì, vì không
  có khái niệm checkpoint nào nói cho ai biết file đó là rác. Đây là kết quả phủ
  định hữu ích nhất: nó cho thấy tính atomic và checkpointing là hai cơ chế riêng
  biệt và cả hai đều phải đúng — một checkpoint trỏ vào một file hỏng thì vô dụng.

- **Bất ngờ: tôi không cần `try/except` ở bất cứ đâu cho nhánh crash.** Cú crash
  là một `SIGKILL` thật, thứ mà Python không thể bắt hay chạy code dọn dẹp. Đó
  chính xác là lý do thiết kế ghi-atomic + checkpoint-sau-khi-commit lại quan
  trọng — nó phải sống sót qua một kiểu thất bại mà tiến trình đang chết có zero
  cơ hội phản ứng, chứ không chỉ một exception bắt được bằng `try/except`. (Nhánh
  "safety timeout" `sys.exit(99)` trong `maybe_crash()` *đúng* là một lối thoát
  kiểu exception bình thường, nhưng nó chỉ kích hoạt nếu driver không kịp gửi
  lệnh giết — và nó đã không kích hoạt ở cả hai lần chạy được ghi lại.)

- **Điều experiment này không chứng minh**: thực thi các bước đồng thời/song
  song, checkpoint ở giữa chừng một bước đắt đỏ, khôi phục sau crash cho các
  side effect không idempotent (lời gọi mạng, thanh toán), hay chính việc kho
  checkpoint bị hỏng (nếu lệnh giết rơi đúng lúc `os.replace` của chính checkpoint
  thì sao? — chưa thử ở đây, dù cùng cơ chế ghi atomic cũng được dùng cho
  `checkpoint.json`, nên lập luận lẽ ra vẫn mở rộng được, nhưng tôi đã không ép
  một cú giết đúng khoảnh khắc đó để kiểm chứng).

Xem file concept [[recovery]] và `experiments/agent-infra/recovery/RUN.md`
/ `diagram.mmd` để đọc bằng chứng mà phần này được chưng cất ra từ đó.
