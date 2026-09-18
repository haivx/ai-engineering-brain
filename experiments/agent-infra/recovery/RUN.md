# RUN.md — checkpoint / resume xuyên qua một lần khởi động lại tiến trình thật

Đây là stdout thật đã ghi lại của `./run.sh` (Python 3.9.6, macOS, chỉ dùng thư
viện chuẩn), chạy từ trạng thái sạch. Không có gì bên dưới là bịa ra — tất cả được
chép nguyên văn từ một phiên terminal thật. `run.sh` khởi chạy `pipeline.py` như
một subprocess thực thụ và giết nó bằng một `SIGKILL` thật (`kill -9`) từ driver,
chứ không phải một thất bại mô phỏng bên trong một lần chạy liên tục; mọi lần
"khởi động lại" bên dưới đều là một tiến trình Python hoàn toàn mới, không chia
sẻ bộ nhớ.

Pipeline 5 bước (`steps.py`): `fetch_input -> validate -> transform ->
aggregate -> write_report`. Mỗi bước commit output của nó một cách atomic (ghi
vào file tạm, `os.fsync`, rồi `os.replace` sang đường dẫn thật) và `pipeline.py`
chỉ ghi thêm tên bước đó vào `checkpoint.json` (cũng được ghi atomic) sau khi lần
commit ấy thành công.

---

## 1. Lần chạy happy-path không gián đoạn (baseline để đem ra so sánh)

Minh họa: một lần chạy sạch, không gián đoạn qua cả 5 bước, tạo ra bản báo cáo
cuối cùng làm chuẩn cùng mã md5 của nó.

```
==== 2. UNINTERRUPTED HAPPY-PATH RUN (baseline for comparison) ====
[23:40:44] STARTUP: no orphaned temp files found
[23:40:44] STARTUP: checkpoint shows completed steps = []
[23:40:44] STEP fetch_input: starting
[23:40:44] STEP fetch_input: committed -> .../recovery/data/step1_input.json
[23:40:44] CHECKPOINT: saved after completing 'fetch_input' -> ['fetch_input']
[23:40:44] STEP validate: starting
[23:40:44] STEP validate: committed -> .../recovery/data/step2_validated.json
[23:40:44] CHECKPOINT: saved after completing 'validate' -> ['fetch_input', 'validate']
[23:40:44] STEP transform: starting
[23:40:44] STEP transform: side effect written to temp file .../data/step3_transformed.json.tmp.42580 (not yet committed)
[23:40:44] STEP transform: committed -> .../recovery/data/step3_transformed.json
[23:40:44] CHECKPOINT: saved after completing 'transform' -> ['fetch_input', 'validate', 'transform']
[23:40:44] STEP aggregate: starting
[23:40:44] STEP aggregate: committed -> .../recovery/data/step4_aggregated.json
[23:40:44] CHECKPOINT: saved after completing 'aggregate' -> ['fetch_input', 'validate', 'transform', 'aggregate']
[23:40:44] STEP write_report: starting
[23:40:44] STEP write_report: committed -> .../recovery/data/step5_report.json
[23:40:44] CHECKPOINT: saved after completing 'write_report' -> ['fetch_input', 'validate', 'transform', 'aggregate', 'write_report']
[23:40:44] PIPELINE COMPLETE
--- baseline final report ---
{
  "report": "sum=30 count=5",
  "final": true
}baseline md5: a2d801bf03cfb3db247cfcff270be67a
```

---

## 2. Crash thật: SIGKILL gửi tới tiến trình giữa bước `transform`

Minh họa: một lệnh `kill -9` thật từ bên ngoài (exit status 137, mã chuẩn cho
"bị giết bởi SIGKILL") rơi xuống sau khi side effect của bước (một file tạm) đã
nằm trên đĩa nhưng *trước* lệnh rename atomic sẽ commit nó và *trước* khi bất kỳ
checkpoint nào cho `transform` được ghi. Đây chính là tình huống bước-làm-dở.

```
==== 4. LAUNCH CHECKPOINTED PIPELINE, INJECT REAL SIGKILL MID 'transform' STEP ====
launched pipeline.py as PID 42589
trigger file observed -> sending SIGKILL to PID 42589 now
process exit status after kill: 137
--- run1.log (first process; killed mid 'transform') ---
[23:40:44] STARTUP: no orphaned temp files found
[23:40:44] STARTUP: checkpoint shows completed steps = []
[23:40:44] STEP fetch_input: starting
[23:40:44] STEP fetch_input: committed -> .../recovery/data/step1_input.json
[23:40:44] CHECKPOINT: saved after completing 'fetch_input' -> ['fetch_input']
[23:40:44] STEP validate: starting
[23:40:44] STEP validate: committed -> .../recovery/data/step2_validated.json
[23:40:44] CHECKPOINT: saved after completing 'validate' -> ['fetch_input', 'validate']
[23:40:44] STEP transform: starting
[23:40:44] STEP transform: side effect written to temp file .../data/step3_transformed.json.tmp.42589 (not yet committed)
[23:40:44] CRASH-INJECT[transform]: side effect (temp file) written to disk; signaling driver via trigger file and waiting to be killed
```

(Tiến trình không kịp ghi log thêm gì nữa — dòng tiếp theo trong mã nguồn,
`os.replace(tmp_path, out_path)`, chưa từng chạy. Đây là `SIGKILL` thật, không
phải một exception bắt được: không có gì trong `pipeline.py` xử lý nó hay có cơ
hội dọn dẹp.)

### Trạng thái trên đĩa sau cú giết, trước mọi lần khởi động lại

Minh họa: một bước làm dở thực sự để lại gì — checkpoint vẫn chỉ liệt kê hai bước
đã commit *trọn vẹn*, còn side effect của bước bị crash sống sót trên đĩa dưới
dạng một file tạm mồ côi, chưa được commit.

```
==== 5. ON-DISK STATE AFTER THE KILL, BEFORE ANY RESTART ====
checkpoint.json:
{
  "completed_steps": [
    "fetch_input",
    "validate"
  ]
}
data/ listing (note the orphaned step3_transformed.json.tmp.* file -- the half-done step):
total 24
drwxr-xr-x@  5 xuanhai  staff  160 Sep  7 23:40 .
drwxr-xr-x@ 11 xuanhai  staff  352 Sep  7 23:40 ..
-rw-r--r--@  1 xuanhai  staff   80 Sep  7 23:40 step1_input.json
-rw-r--r--@  1 xuanhai  staff   76 Sep  7 23:40 step2_validated.json
-rw-r--r--@  1 xuanhai  staff   56 Sep  7 23:40 step3_transformed.json.tmp.42589
```

---

## 3. Khởi động lại: một tiến trình hoàn toàn mới resume từ checkpoint gần nhất

Minh họa: đây là một lần gọi `python3 pipeline.py` mới tinh (PID mới) không chia
sẻ bộ nhớ gì với tiến trình đã bị giết. Nó đọc `checkpoint.json` từ đĩa, vứt bỏ
file tạm mồ côi của bước làm dở (câu trả lời ở đây là tính-lại-idempotent, xem
NOTES.md), **bỏ qua** `fetch_input` và `validate` (không làm lại), và chạy lại
`transform` từ đầu cho tới khi hoàn tất.

```
==== 6. RESTART: BRAND NEW PROCESS RESUMES FROM LAST CHECKPOINT ====
--- run2.log (second, new process; resumes) ---
[23:40:44] STARTUP: found orphaned temp file from a half-done step -> .../data/step3_transformed.json.tmp.42589 (removing; the real output was never renamed to it, so nothing referenced it)
[23:40:44] STARTUP: checkpoint shows completed steps = ['fetch_input', 'validate']
[23:40:44] STEP fetch_input: SKIP (already completed per checkpoint)
[23:40:44] STEP validate: SKIP (already completed per checkpoint)
[23:40:44] STEP transform: starting
[23:40:44] STEP transform: side effect written to temp file .../data/step3_transformed.json.tmp.42595 (not yet committed)
[23:40:44] STEP transform: committed -> .../recovery/data/step3_transformed.json
[23:40:44] CHECKPOINT: saved after completing 'transform' -> ['fetch_input', 'validate', 'transform']
[23:40:44] STEP aggregate: starting
[23:40:44] STEP aggregate: committed -> .../recovery/data/step4_aggregated.json
[23:40:44] CHECKPOINT: saved after completing 'aggregate' -> ['fetch_input', 'validate', 'transform', 'aggregate']
[23:40:44] STEP write_report: starting
[23:40:44] STEP write_report: committed -> .../recovery/data/step5_report.json
[23:40:44] CHECKPOINT: saved after completing 'write_report' -> ['fetch_input', 'validate', 'transform', 'aggregate', 'write_report']
[23:40:44] PIPELINE COMPLETE
```

---

## 4. Phép kiểm tra bằng nhau: kết quả sau resume so với kết quả happy-path không gián đoạn

Minh họa: toàn bộ ý nghĩa của checkpointing — lần chạy crash-rồi-resume tạo ra
artifact cuối cùng giống từng byte với lần chạy không hề gián đoạn, dù nó đã hứng
một cú giết thật ở giữa chừng.

```
==== 7. VERIFY: RESUMED RESULT == UNINTERRUPTED HAPPY-PATH RESULT ====
--- resumed final report ---
{
  "report": "sum=30 count=5",
  "final": true
}baseline md5: a2d801bf03cfb3db247cfcff270be67a
resumed  md5: a2d801bf03cfb3db247cfcff270be67a
RESULT: MATCH -- resumed run produced byte-identical output to the uninterrupted run
```

---

## 5. Đối chứng: baseline không checkpoint khởi động lại từ số không

Minh họa: cùng cú crash đó tiêm vào `no_checkpoint_pipeline.py` (cùng 5 bước,
cùng điểm crash, nhưng nó không bao giờ đọc hay ghi checkpoint). Tiến trình đầu
tiên chết y hệt (SIGKILL, exit 137) sau khi `fetch_input` và `validate` đã chạy
xong. Khi khởi động lại, vì không có bản ghi nào về chuyện đã xảy ra,
**`fetch_input` và `validate` chạy lại** — đúng sự lãng phí mà checkpointing sinh
ra để loại bỏ.

```
==== 8. CONTRAST: NO-CHECKPOINT BASELINE, SAME CRASH, RESTARTS FROM ZERO ====
launched no_checkpoint_pipeline.py as PID 42603
trigger file observed -> sending SIGKILL to PID 42603 now
process exit status after kill: 137
--- run3.log (no-checkpoint, first process; killed mid 'transform') ---
[23:40:45] STARTUP: no checkpoint file is ever read -- always starting at step 1
[23:40:45] STEP fetch_input: running (no checkpoint to skip against)
[23:40:45] STEP fetch_input: starting
[23:40:45] STEP fetch_input: committed -> .../recovery/data/step1_input.json
[23:40:45] STEP validate: running (no checkpoint to skip against)
[23:40:45] STEP validate: starting
[23:40:45] STEP validate: committed -> .../recovery/data/step2_validated.json
[23:40:45] STEP transform: running (no checkpoint to skip against)
[23:40:45] STEP transform: starting
[23:40:45] STEP transform: side effect written to temp file .../data/step3_transformed.json.tmp.42603 (not yet committed)
[23:40:45] CRASH-INJECT[transform]: side effect (temp file) written to disk; signaling driver via trigger file and waiting to be killed

restarting no-checkpoint pipeline...
```

**Một tác dụng phụ tới giờ chưa được ghi lại, đáng nêu rõ**: cú SIGKILL ở trên rơi xuống sau khi `no_checkpoint_pipeline.py` đã ghi `data/step3_transformed.json.tmp.<pid>` (cùng cơ chế file tạm mà `steps.py` dùng ở mọi nơi). Vì `no_checkpoint_pipeline.py` không có bước dọn dẹp lúc khởi động (khác với `pipeline.py`, vốn glob và xóa `data/*.tmp.*` ở mỗi lần khởi chạy — xem `clean_orphaned_temp_files` ở mục 3), file tạm mồ côi đó không bao giờ bị thứ gì trong thiết kế này xóa đi. `run4` bên dưới tạo file tạm mới của riêng nó cho `transform` và commit bình thường, nhưng file lạc từ cú crash của `run3` cứ nằm lại trong `data/` vô thời hạn — qua mỗi cú crash tương lai của baseline này, rác chỉ ngày một nhiều. Điều này quan sát được trực tiếp trong lượt chạy `./run.sh` đầy đủ thứ hai (`data/step3_transformed.json.tmp.42704`, phát hiện khi rà soát) và là cặn bã crash thật, không phải bug của harness. Nó không xuất hiện trong ảnh chụp `data/` ở trạng thái nghỉ được commit kèm file này, vì ảnh chụp đó được tạo ra bởi một chu kỳ crash+resume `pipeline.py` riêng, muộn hơn, mà lệnh reset `rm -rf data` của nó đã xóa sạch — xem "Trạng thái nghỉ trên đĩa" ở cuối file này.

```
--- run4.log (no-checkpoint, restart -- note fetch_input and validate re-run too) ---
[23:40:45] STARTUP: no checkpoint file is ever read -- always starting at step 1
[23:40:45] STEP fetch_input: running (no checkpoint to skip against)
[23:40:45] STEP fetch_input: starting
[23:40:45] STEP fetch_input: committed -> .../recovery/data/step1_input.json
[23:40:45] STEP validate: running (no checkpoint to skip against)
[23:40:45] STEP validate: starting
[23:40:45] STEP validate: committed -> .../recovery/data/step2_validated.json
[23:40:45] STEP transform: running (no checkpoint to skip against)
[23:40:45] STEP transform: starting
[23:40:45] STEP transform: side effect written to temp file .../data/step3_transformed.json.tmp.42607 (not yet committed)
[23:40:45] STEP transform: committed -> .../recovery/data/step3_transformed.json
[23:40:45] STEP aggregate: running (no checkpoint to skip against)
[23:40:45] STEP aggregate: starting
[23:40:45] STEP aggregate: committed -> .../recovery/data/step4_aggregated.json
[23:40:45] STEP write_report: running (no checkpoint to skip against)
[23:40:45] STEP write_report: starting
[23:40:45] STEP write_report: committed -> .../recovery/data/step5_report.json
[23:40:45] PIPELINE COMPLETE
```

---

## 6. Cái giá của một bước không atomic (cùng kiểu giết, không temp+rename)

Minh họa: câu trả lời của `pipeline.py` cho "chuyện gì xảy ra với một bước làm dở"
là commit atomic (file tạm + `os.replace`). `unsafe_step_demo.py` cho thấy lựa
chọn còn lại: ghi thẳng vào đường dẫn output thật theo hai mảnh. Cùng kiểu
`SIGKILL` từ bên ngoài, rơi vào giữa hai mảnh, để lại file **thật** hỏng vĩnh
viễn — ở đây không có file tạm mồ côi nào để vứt đi, thiệt hại giáng đúng vào
artifact quan trọng.

```
==== 9. COST OF A NON-ATOMIC STEP: SAME KIND OF KILL, NO TEMP+RENAME ====
launched unsafe_step_demo.py as PID 42612
trigger file observed -> sending SIGKILL to PID 42612 now
process exit status after kill: 137
--- run5.log ---
[23:40:45] UNSAFE STEP: writing directly to the final path (no temp file, no atomic rename)
[23:40:45] UNSAFE STEP: first chunk committed straight to the REAL file; signaling driver and waiting to be killed

unsafe_output.json contents (expect truncated / invalid JSON, permanently):
{"values": [2, 4, 6, 

JSON PARSE FAILED as expected: the real file was corrupted by a non-atomic write + kill, and nothing in this design would ever fix it -- unlike steps.py's temp+rename, which never touches the real path until it's whole
```

---

## Khả năng tái lập

Toàn bộ chuỗi ở trên đã được chạy lại lần thứ hai từ trạng thái sạch (`./run.sh`)
và cho ra kết quả y hệt tại mọi điểm kiểm tra: cùng mẫu bỏ qua bước, cùng
`RESULT: MATCH` ở bước 7, cùng kiểu hỏng file ở bước 9 (PID khác nhau giữa các lần
chạy, mọi thứ còn lại đều deterministic). Chính lượt chạy thứ hai đó đã tạo ra file
tạm mồ côi của `no_checkpoint_pipeline.py` bàn ở mục 5 phía trên.

---

## Trạng thái nghỉ trên đĩa (thứ đang thực sự nằm trong thư mục này lúc này)

`checkpoint.json` và `data/*.json` ở trạng thái nghỉ phản ánh một pipeline **đã
hoàn tất trọn vẹn, đã resume xong**: `checkpoint.json` liệt kê đủ 5 bước, và
`data/` chỉ giữ 5 output cuối đã commit — không có file `*.tmp.*` nào, vì chúng
được tạo ra bởi một chu kỳ crash+resume nữa chạy có chủ đích để để lại một ảnh
chụp cuối cùng sạch sẽ, và bước khởi động của `pipeline.py` xóa các file tạm mồ
côi ngay ở lần khởi chạy kế tiếp (đó chính là dòng log "removing; the real output
was never renamed to it" ở mục 3 phía trên). Trạng thái đĩa lúc giữa crash, còn
file mồ côi, chỉ được bảo tồn trong các bản ghi terminal của file này (output
`ls -la` ở mục 2) và trong `run1.log`/`run2.log` — không phải dưới dạng một
artifact thường trực, vì không có gì trong thiết kế của `pipeline.py` nhằm giữ nó
lại qua lần chạy kế tiếp.

Hai (thực ra là ba) sự thật liên quan đáng nói rõ, vì chúng đọc ra khác nhau tùy
bạn đang nhìn script nào:

- **`pipeline.py` chủ động dọn các file `.tmp.*` cũ ở mỗi lần khởi động** — nó
  không chỉ đơn thuần lờ chúng đi. Đây là sự gọn gàng có chủ đích, không phải yêu
  cầu về tính đúng đắn (dù sao cũng chẳng gì đọc các đường dẫn đó).
- **`no_checkpoint_pipeline.py` không có bước dọn dẹp nào và sẽ không bao giờ có**
  — bất kỳ file tạm nào nó bỏ mồ côi qua một cú crash giữa `transform` đều nằm
  trong `data/` vĩnh viễn, tích tụ qua từng lần crash. Xem mục 5 ở trên để thấy
  trường hợp quan sát được trực tiếp.
- **`crash_trigger`** (ở gốc repo) là một file IPC sống, chỉ dành cho driver: tiến
  trình con sắp crash chạm vào nó để báo với `run.sh` rằng "một side effect đã bắt
  đầu, giết tôi ngay đi", và mỗi giai đoạn trong `run.sh` đều xóa nó trước khi tạo
  lại mới. Nó vô nghĩa một khi `run.sh` thoát, nên một dòng dọn dẹp cuối đã được
  thêm vào cuối driver để xóa nó, thay vì để lại cặn bã tín hiệu khó hiểu trên đĩa
  sau khi một lần chạy đầy đủ kết thúc.
