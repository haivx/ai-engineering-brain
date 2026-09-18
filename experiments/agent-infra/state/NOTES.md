# NOTES.md — state/ (working state trong một lần chạy)

- Tách `working.json` (bị ghi đè) khỏi `log.jsonl` (append-only) không tốn
  thêm gì trong code — ghi log chỉ là một dòng thêm cho mỗi bước. Kỷ luật
  này rẻ; chính *thói quen* làm điều đó mới là phần thực hành thật sự, chứ
  không phải cơ chế.
- Bản chứng minh chỉ đứng vững vì "durable" đã được định nghĩa hẹp và trung
  thực: append-only, một file, không bao giờ bị cắt cụt, không bao giờ bị
  ghi lại. Ngay khoảnh khắc một kho "durable" cũng bị `overwrite` (như
  anti-pattern blob), nó thôi không còn durable trên thực tế nữa, dù bạn có
  gọi tên nó như thế.
- Bước dựng lại (`reconstruct`) đang làm việc thật: nó không chỉ là "log vẫn
  còn dữ liệu", mà là "bạn có thể suy ra đúng điểm resume (bước 4) thuần túy
  từ những gì đã commit" — đó mới là lợi ích vận hành thật, chứ không phải
  chỉ "không mất dữ liệu" một cách trừu tượng.
- Anti-pattern (`blob.json`) mới là nửa hữu ích hơn của bài tập này. Nó không
  phải hình nộm — nó chính là bản nháp đầu tiên mà ai cũng viết ("cứ đổ hết
  state vào một file JSON"), và nó hỏng âm thầm: chẳng có gì trông sai cho
  tới đúng khoảnh khắc crash + dọn dẹp.
- Bất ngờ: trường `history` của thiết kế blob, khi còn tồn tại, thực ra trông
  *hay hơn* thiết kế tách tầng ở giữa lần chạy (nó chứa nhiều thông tin hơn
  hẳn, ngay trong một file). Thất bại vô hình cho tới khi cú xóa sạch xảy ra
  — điều này đáng nhấn mạnh trong đoạn concept, vì "trông ổn trong phần lớn
  thời gian" chính là lý do sai lầm này cứ tồn tại mãi.
- Để có tính deterministic thì phải loại bỏ mọi yếu tố đồng hồ hệ thống/ngẫu
  nhiên — phép `step * step` đóng vai "phần tính toán" thay cho một phép biến
  đổi deterministic thật. Trong một lần chạy agent thật, tầng working-state sẽ
  giữ những thứ như buffer output LLM dang dở hay các tham số scratch của
  tool-call; log sẽ chỉ giữ kết quả đã commit của mỗi bước hoàn tất, cùng hình
  dạng như ở đây.
- Điều experiment này KHÔNG chứng minh: nó không cho thấy khả năng *recovery*
  tự động (chạy tiếp từ bước 4 và hoàn tất bước 4-5) — chỉ cho thấy thông tin
  cần để làm điều đó sống sót qua cú xóa sạch. Hành vi resume-from-checkpoint
  thật sự thuộc về `experiments/agent-infra/recovery/`, không phải ở đây — thư
  mục này chứng minh dữ liệu sống sót, chứ không phải một tiến trình tự động
  nhặt nó lên dùng tiếp.
- Một-file-cho-một-tầng là một ràng buộc thật đáng giữ: không lúc nào script
  cần biết schema của file thuộc tầng *kia* để làm việc của mình, và chính điều
  đó khiến việc xóa sạch riêng một tầng vừa an toàn (với log) vừa đọc ra được
  như một thất bại (với blob).
