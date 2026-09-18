# Đầu vào cho playbooks/build-eval-set.md

Những điểm bổ sung học được khi dựng `experiments/agent-infra/observability/`.
Viết theo đúng giọng các bước đánh số ngắn gọn của playbook. Người biên tập
concept nên hợp nhất chúng vào — không lặp lại bước 1-6 hay phần Nguyên tắc đã có sẵn.

## Bổ sung cho danh sách "Các bước" (logging có cấu trúc, không dùng lệnh print)

7. Ghi log mọi case dưới dạng bản ghi có cấu trúc (JSONL), không phải lệnh
   print — mỗi dòng một object JSON, mỗi bước một dòng. Mỗi bản ghi cần ít
   nhất: `run_id` (dùng chung cho mọi bản ghi trong một lần gọi harness),
   `case_id` (dùng chung cho mọi bản ghi của một test case), `step` (giai đoạn
   nào sinh ra bản ghi này), `status` (`ok` / `error` — tuyệt đối đừng gộp
   "trả lời sai" và "crash" vào cùng một rổ), `duration_ms`, và `error`
   (`null` trừ khi `status` là `error`).
   `run_id` + `case_id` đi cùng nhau chính là thứ cho phép bạn `grep` một lỗi
   ngược về trace đầy đủ từng bước của nó, thay vì phải chạy lại với print cắm thêm.

8. Cho mỗi giai đoạn pipeline một bản ghi riêng, không chỉ một pass/fail cuối
   cùng cho mỗi case. Một case có 4 bước nội bộ mà crash ở bước 1 phải hiện ra
   `step: "<tên_giai_đoạn>"` tại điểm thất bại — một bản ghi "case failed" duy
   nhất không cho bạn biết cú crash xảy ra trước hay sau khi model được gọi.

9. Trước khi đổi bất cứ thứ gì, hãy lưu bản tóm tắt kết quả eval vào một file
   đặt theo một tag ngắn (`results/eval_<tag>.json`), không chỉ in ra stdout.
   Bạn cần số liệu của lần chạy trước nằm trên đĩa để đem ra diff, chứ không
   phải trôi trong màn hình terminal.

## Bổ sung cho phần "Nguyên tắc" (kỷ luật so sánh trước/sau)

- Khi kiểm tra xem một thay đổi (ngưỡng, prompt, đổi model) có giúp ích không,
  hãy đổi đúng một biến giữa hai lần chạy và diff các file kết quả đã lưu, chứ
  đừng chỉ so hai con số pass-rate tổng. Một con số "+X%" đơn lẻ có thể che giấu
  một sự hòa vốn — ví dụ N case mới pass và M case khác mới fail. Hãy báo cáo cả
  mức chênh ròng lẫn danh sách case bị lật (case nào, lật theo hướng nào, đáp án
  cũ so với đáp án mới) để cả "cái này có giúp ích không" lẫn "nó đánh đổi mất
  gì" đều được trả lời từ cùng một bảng.
- Hãy xác minh rằng bộ eval thực sự nhạy với biến bạn đang kiểm tra trước khi
  tin vào một phép so sánh: nếu trước/sau không có case nào bị lật, bộ eval
  không hề động tới biến đó và phép so sánh chẳng chứng minh được gì — hãy sửa
  lại bộ case, đừng báo cáo kết quả rỗng đó thành "không có regression".
- Con số pass-rate và log có cấu trúc trả lời hai câu hỏi khác nhau: con số cho
  biết hỏng bao nhiêu, log cho biết hỏng ở case nào và vì sao. Giữ cả hai — một
  điểm số tổng trần trụi không có trace theo từng case, từng bước đứng sau thì
  không đủ để debug một regression, chỉ đủ để phát hiện ra nó.
