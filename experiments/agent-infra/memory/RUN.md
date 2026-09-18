# RUN.md — bằng chứng về session state xuyên nhiều lần chạy vs. log durable

Môi trường: Python 3.9.6, chỉ dùng thư viện chuẩn. Chạy từ
`experiments/agent-infra/memory/` (hoặc từ gốc repo — các đường dẫn trong `run.py`
đều neo theo thư mục của chính script). `SESSION_MAX_RUNS = 2`, nên 3 lần gọi
riêng biệt là đủ để thấy một session tích lũy, hết hạn, rồi bị thay thế.

Mỗi lệnh `python3 run.py run` bên dưới là một **lần gọi tiến trình riêng biệt** —
đây có chủ đích là bằng chứng xuyên nhiều lần chạy, không phải xuyên nhiều bước như `state/`.

Toàn bộ output bên dưới được chép nguyên văn từ các lần chạy `run.py` thật trên terminal.

---

## Lần chạy #1 — tạo session mới

Minh họa: khi không có `session.json` trên đĩa, một session mới (`S1`) được tạo;
id của nó được suy ra một cách deterministic từ số sự kiện `session_start` đã có
trong `log.jsonl` (ở đây là không có), chứ không từ đồng hồ hệ thống. Cả hai tầng
đều được cập nhật: `log.jsonl` được ghi thêm, và `session.json` được ghi mới.

```
=== reset to clean slate ===
[reset] removed: nothing (already clean)

=== RUN #1 (fresh process invocation) ===
[session] no session.json found -> starting new session S1
[log.jsonl] appended durable 'run' event -> session=S1 run_index=1
[session.json] updated -> session=S1 run_count=1 (still alive, will expire at run_count=2)

=== show after run #1 ===
=== session.json (session/plan state) ===
{
  "facts": [
    "fact-from-run-1-of-S1"
  ],
  "run_count": 1,
  "session_id": "S1"
}
=== log.jsonl (durable log, all sessions, all runs) ===
  {"event": "session_start", "session_id": "S1"}
  {"event": "run", "fact": "fact-from-run-1-of-S1", "run_index": 1, "session_id": "S1"}
=== totals: 2 durable log record(s) ===
```

---

## Lần chạy #2 — session tiếp tục, rồi chạm giới hạn tuổi thọ và hết hạn

Minh họa: lần gọi thứ hai nhặt `session.json` lên và tiếp tục `S1` (`run_count`
1 -> 2). Việc chạm `SESSION_MAX_RUNS` ngay trong lần chạy này kích hoạt
**promotion**: một bản ghi `session_summary` mang toàn bộ dữ kiện tích lũy của
`S1` được ghi thêm vào log durable, và chỉ sau đó `session.json` mới bị xóa.
State của session không bị mất âm thầm — nó được gấp vào hồ sơ vĩnh viễn trước
khi bản sao ephemeral biến mất.

```
=== RUN #2 (fresh process invocation, session S1 continues and hits SESSION_MAX_RUNS) ===
[session] continuing existing session S1 (run_count so far: 1)
[log.jsonl] appended durable 'run' event -> session=S1 run_index=2
[log.jsonl] appended 'session_summary' -> session S1 reached SESSION_MAX_RUNS=2; facts promoted to durable log
[session] session.json DELETED — session S1's state no longer exists anywhere except as the summary just promoted into log.jsonl

=== show after run #2 (session.json should now be gone -- expired + promoted) ===
=== session.json (session/plan state) ===
  <absent — no active session right now>
=== log.jsonl (durable log, all sessions, all runs) ===
  {"event": "session_start", "session_id": "S1"}
  {"event": "run", "fact": "fact-from-run-1-of-S1", "run_index": 1, "session_id": "S1"}
  {"event": "run", "fact": "fact-from-run-2-of-S1", "run_index": 2, "session_id": "S1"}
  {"event": "session_summary", "facts": ["fact-from-run-1-of-S1", "fact-from-run-2-of-S1"], "session_id": "S1", "total_runs": 2}
=== totals: 4 durable log record(s) ===
```

---

## Lần chạy #3 — một session hoàn toàn mới bắt đầu; log durable giờ trải qua cả hai session

Minh họa khẳng định về tích lũy xuyên nhiều lần chạy: khi `session.json` đã biến
mất, lần gọi thứ ba bắt đầu một session mới (`S2` — suy ra từ việc `log.jsonl`
giờ đã chứa một sự kiện `session_start` trước đó). Lịch sử của `S1` nằm nguyên vẹn
trong `log.jsonl`; các sự kiện mới của `S2` chỉ đơn giản được ghi thêm phía sau.
Log durable giờ chứa toàn bộ lịch sử có thứ tự của cả hai session qua cả 3 lần
chạy; `session.json` chỉ phản ánh session đang sống.

```
=== RUN #3 (fresh process invocation, session S1 is gone -> a NEW session S2 starts) ===
[session] no session.json found -> starting new session S2
[log.jsonl] appended durable 'run' event -> session=S2 run_index=1
[session.json] updated -> session=S2 run_count=1 (still alive, will expire at run_count=2)

=== show after run #3 (durable log now spans BOTH sessions S1 and S2 across all 3 runs) ===
=== session.json (session/plan state) ===
{
  "facts": [
    "fact-from-run-1-of-S2"
  ],
  "run_count": 1,
  "session_id": "S2"
}
=== log.jsonl (durable log, all sessions, all runs) ===
  {"event": "session_start", "session_id": "S1"}
  {"event": "run", "fact": "fact-from-run-1-of-S1", "run_index": 1, "session_id": "S1"}
  {"event": "run", "fact": "fact-from-run-2-of-S1", "run_index": 2, "session_id": "S1"}
  {"event": "session_summary", "facts": ["fact-from-run-1-of-S1", "fact-from-run-2-of-S1"], "session_id": "S1", "total_runs": 2}
  {"event": "session_start", "session_id": "S2"}
  {"event": "run", "fact": "fact-from-run-1-of-S2", "run_index": 1, "session_id": "S2"}
=== totals: 6 durable log record(s) ===
```

---

## Kiểm tra khả năng tái lập

Minh họa: `reset` rồi chạy lại đúng chuỗi 3 lần chạy đó cho ra output giống nhau
từng byte mọi lúc — session id và các dữ kiện chỉ được suy ra từ nội dung log
trước đó, không bao giờ từ thời gian hệ thống hay yếu tố ngẫu nhiên.

```
$ python3 run.py reset
[reset] removed: ['session.json', 'log.jsonl']
$ python3 run.py run; python3 run.py run; python3 run.py run    # > /tmp/mem_repro1.txt
$ python3 run.py reset
[reset] removed: ['session.json', 'log.jsonl']
$ python3 run.py run; python3 run.py run; python3 run.py run    # > /tmp/mem_repro2.txt
$ diff /tmp/mem_repro1.txt /tmp/mem_repro2.txt && echo "REPRODUCIBLE: identical output across clean 3-run sequences"
REPRODUCIBLE: identical output across clean 3-run sequences
```

Các file được sinh ra (`session.json`, `log.jsonl`) là build artifact của việc
chạy demo — chúng bị xóa bởi `python3 run.py reset` và không nhằm mục đích commit
như bằng chứng cố định; chính các bản ghi terminal ở trên mới là hồ sơ durable.
