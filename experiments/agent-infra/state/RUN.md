# RUN.md — bằng chứng về working state trong một lần chạy

Môi trường: Python 3.9.6, chỉ dùng thư viện chuẩn. Chạy từ
`experiments/agent-infra/state/` (hoặc từ gốc repo — các đường dẫn trong `run.py`
đều neo theo thư mục của chính script).

Toàn bộ output bên dưới được chép nguyên văn từ các lần chạy `run.py` thật trên terminal.

---

## 1. Lần chạy bình thường: hai tầng, ghi vào hai file riêng biệt

Minh họa: `working.json` bị ghi đè ở mỗi bước (scratch thuần túy, không nhớ gì về
lịch sử của chính nó); `log.jsonl` được ghi thêm ở mỗi bước (durable, không bao
giờ bị ghi lại). Sau lần chạy, `working.json` chỉ phản ánh trạng thái cuối cùng
(chẳng chứng minh được gì ở đó), còn `log.jsonl` giữ mỗi bước một dòng.

```
=== SECTION 1: normal run, two tiers written separately ===
[run] starting run_id=R1, 5 steps, tiers: working.json (ephemeral) + log.jsonl (durable)
  [working.json] overwritten -> current_step=1 (scratch only, no history kept here)
  [log.jsonl]     appended    -> step=1 result=1 (committed, permanent)
  [working.json] overwritten -> current_step=2 (scratch only, no history kept here)
  [log.jsonl]     appended    -> step=2 result=4 (committed, permanent)
  [working.json] overwritten -> current_step=3 (scratch only, no history kept here)
  [log.jsonl]     appended    -> step=3 result=9 (committed, permanent)
  [working.json] overwritten -> current_step=4 (scratch only, no history kept here)
  [log.jsonl]     appended    -> step=4 result=16 (committed, permanent)
  [working.json] overwritten -> current_step=5 (scratch only, no history kept here)
  [log.jsonl]     appended    -> step=5 result=25 (committed, permanent)
[run] run_id=R1 completed all 5 steps normally.

=== contents of working.json after normal completion ===
{
  "current_step": 5,
  "run_id": "R1",
  "scratch": {},
  "status": "done"
}
=== contents of log.jsonl after normal completion ===
{"event": "step_complete", "result": 1, "run_id": "R1", "step": 1}
{"event": "step_complete", "result": 4, "run_id": "R1", "step": 2}
{"event": "step_complete", "result": 9, "run_id": "R1", "step": 3}
{"event": "step_complete", "result": 16, "run_id": "R1", "step": 4}
{"event": "step_complete", "result": 25, "run_id": "R1", "step": 5}
```

---

## 2. Ép crash + xóa sạch working state + dựng lại từ log durable

Minh họa khẳng định ranh giới cốt lõi: một lần chạy (`R2`) bị ép crash sau bước 3
(`--crash-at 3`), để lại `working.json` lơ lửng với dữ liệu scratch đang dở. Sau
đó `working.json` bị xóa thẳng (`wipe-working`, mô phỏng tiến trình chết /
container bị recycle). Tiến độ của lần chạy sau đó được dựng lại đầy đủ **chỉ**
từ `log.jsonl` — chứng minh rằng xóa sạch tầng ephemeral không làm mất bất cứ thứ
gì đã được commit.

```
=== SECTION 2: simulate crash mid-run (run_id=R2, crash after step 3) ===
[run] starting run_id=R2, 5 steps, tiers: working.json (ephemeral) + log.jsonl (durable)
  [working.json] overwritten -> current_step=1 (scratch only, no history kept here)
  [log.jsonl]     appended    -> step=1 result=1 (committed, permanent)
  [working.json] overwritten -> current_step=2 (scratch only, no history kept here)
  [log.jsonl]     appended    -> step=2 result=4 (committed, permanent)
  [working.json] overwritten -> current_step=3 (scratch only, no history kept here)
  [log.jsonl]     appended    -> step=3 result=9 (committed, permanent)
  !! SIMULATED CRASH after step 3 (run_id=R2) — process exits, working.json left dangling
(exit code: 1)

=== working.json left dangling after the crash ===
{
  "current_step": 3,
  "run_id": "R2",
  "scratch": {
    "computing_result_for_step": 3
  },
  "status": "in_progress"
}
=== SIMULATE PROCESS DEATH / CONTAINER RECYCLE: wipe working.json ===
[wipe-working] working.json deleted (simulates process death / container recycle).

=== working.json now: GONE ===

=== reconstruct R2's progress from the durable log ALONE ===
[reconstruct] working.json present? False
[reconstruct] recovered 3 completed step(s) for run_id=R2 from log.jsonl alone:
    step 1 -> result 1
    step 2 -> result 4
    step 3 -> result 9
[reconstruct] conclusion: last confirmed step = 3/5; a resumer would restart at step 4. No data was lost even though the ephemeral tier is gone.
```

---

## 3. Sai lầm ngược lại: thiết kế gộp-một-khối mất sạch lịch sử với cùng cú xóa

Minh họa chính xác thứ mà việc tách tầng đang ngăn chặn. `blob-run` gộp cả scratch
state LẪN toàn bộ lịch sử vào **một** file (`blob.json`), bị ghi đè ở mỗi bước —
đúng thiết kế mặc định của nhiều hệ thống kiểu "cứ quăng vào một file là xong". Nó
bị ép crash ở đúng điểm đó (bước 3) và bị xóa theo cùng cách. Vì chưa từng tồn tại
một kho append-only riêng, cú xóa phá hủy kết quả của cả 3 bước đã hoàn tất, không
chỉ bước đang dở.

```
=== SECTION 3: ANTI-PATTERN — single blob.json merges scratch + history ===
[blob-run] starting run_id=R3 using ANTI-PATTERN single blob.json (scratch + history merged)
  [blob.json] overwritten -> current_step=1, history now has 1 entrie(s)
  [blob.json] overwritten -> current_step=2, history now has 2 entrie(s)
  [blob.json] overwritten -> current_step=3, history now has 3 entrie(s)
  !! SIMULATED CRASH after step 3 (run_id=R3) — blob.json is the only record of progress
(exit code: 1)

=== blob.json right after the crash (note: it DOES contain full history so far) ===
{
  "current_step": 3,
  "history": [
    {
      "result": 1,
      "step": 1
    },
    {
      "result": 4,
      "step": 2
    },
    {
      "result": 9,
      "step": 3
    }
  ],
  "run_id": "R3",
  "status": "in_progress"
}
=== SAME kind of process death: wipe blob.json ===
[wipe-blob] blob.json deleted (same kind of process death as wipe-working).
[wipe-blob] conclusion: 3 previously-completed step result(s) are GONE. There is no separate durable store to recover from, because scratch state and history were never separated.

=== blob.json now: GONE ===
=== there is no separate durable log for the blob design -- nothing to reconstruct from ===
```

---

## 4. Kiểm tra khả năng tái lập

Minh họa: toàn bộ bản chứng minh là deterministic — `reset` rồi chạy lại đúng
chuỗi lệnh đó sẽ cho output giống nhau từng byte, lần nào cũng vậy, từ một trạng
thái sạch (không có timestamp đồng hồ hệ thống hay yếu tố ngẫu nhiên nào trong `run.py`).

```
$ python3 run.py reset
[reset] removed: ['log.jsonl']
$ python3 run.py run --run-id R1 > /tmp/repro1.txt
$ python3 run.py reset
[reset] removed: ['working.json', 'log.jsonl']
$ python3 run.py run --run-id R1 > /tmp/repro2.txt
$ diff /tmp/repro1.txt /tmp/repro2.txt && echo "REPRODUCIBLE: identical output across clean runs"
REPRODUCIBLE: identical output across clean runs
```

Các file được sinh ra (`working.json`, `log.jsonl`, `blob.json`) là build artifact
của việc chạy demo — chúng bị xóa bởi `python3 run.py reset` và không nhằm mục đích
commit như bằng chứng cố định; chính các bản ghi terminal ở trên mới là hồ sơ durable.
