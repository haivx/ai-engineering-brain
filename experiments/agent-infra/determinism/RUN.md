# RUN.md — output terminal đã ghi lại

Môi trường: Python 3.9.6, chỉ dùng thư viện chuẩn, chạy từ thư mục này bằng
`python3 <script>.py`. Toàn bộ output bên dưới được copy-paste từ các lần chạy
thật, không bịa ra.

---

## 1. Ranh giới có kỷ luật — log deterministic vẫn giống nhau từng byte

Minh họa: cùng một input chạy hai lần qua `boundary.run_pipeline()`. Log `nd`
(ranh giới bất định) khác nhau ở mỗi lần chạy; log `deterministic` (lắp ráp
input, parse, quyết định) thì giống nhau từng byte, có một phép diff tường minh
chứng minh điều đó.

```
$ python3 run_stable.py
=== Run 1: deterministic log ===
{
  "assemble_input": "REQUEST\nreason: urgent prod incident\nrequester: alice\nresource: db-prod-01",
  "decide": {
    "action": "grant_access",
    "reason": "model approved request"
  },
  "parse_output": {
    "label": "APPROVE"
  }
}

=== Run 2: deterministic log ===
{
  "assemble_input": "REQUEST\nreason: urgent prod incident\nrequester: alice\nresource: db-prod-01",
  "decide": {
    "action": "grant_access",
    "reason": "model approved request"
  },
  "parse_output": {
    "label": "APPROVE"
  }
}

=== Run 1: non-deterministic (boundary) log ===
{
  "boundary_call": {
    "latency_ms": 235,
    "raw_confidence": 0.94,
    "raw_text": "This should be approved; it is policy-compliant."
  }
}

=== Run 2: non-deterministic (boundary) log ===
{
  "boundary_call": {
    "latency_ms": 198,
    "raw_confidence": 0.776,
    "raw_text": "Approved. This satisfies the policy requirements."
  }
}

=== Diff: deterministic logs (run1 vs run2) ===
(no diff -- byte-identical)

=== Diff: non-deterministic logs (run1 vs run2) ===
--- run1.nd
+++ run2.nd
@@ -1,7 +1,7 @@
 {
   "boundary_call": {
-    "latency_ms": 235,
-    "raw_confidence": 0.94,
-    "raw_text": "This should be approved; it is policy-compliant."
+    "latency_ms": 198,
+    "raw_confidence": 0.776,
+    "raw_text": "Approved. This satisfies the policy requirements."
   }
 }


=== Summary ===
deterministic logs byte-identical: True
non-deterministic logs byte-identical: False
final decision run1: {'action': 'grant_access', 'reason': 'model approved request'}
final decision run2: {'action': 'grant_access', 'reason': 'model approved request'}
```

---

## 2. Tính bất định bị rò rỉ — kiểu thất bại, rồi phần đối chứng

Minh họa ba cách tính bất định lọt qua ranh giới vào đoạn code trông có vẻ
deterministic (parse ngây thơ bám vào cách diễn đạt tình cờ; một timestamp đồng
hồ hệ thống đóng dấu vào bản ghi quyết định; thứ tự duyệt `set()` giữa các lần
gọi tiến trình), rồi chạy lại pipeline có kỷ luật trên cùng input/áp lực đó để
đối chứng trực tiếp.

```
$ python3 leak_demo.py
=== Leak 1 + 2: naive parse + timestamped decide, same input, two runs ===

--- run1 'deterministic-looking' log ---
{
  "assemble_input": "REQUEST\nreason: urgent prod incident\nrequester: alice\nresource: db-prod-01",
  "decide": {
    "action": "deny_access",
    "decided_at": 1788799391.64189
  },
  "parse_output": {
    "label": "UNKNOWN"
  },
  "tag_summary": "urgent,oncall,db,prod,incident"
}

--- run2 'deterministic-looking' log ---
{
  "assemble_input": "REQUEST\nreason: urgent prod incident\nrequester: alice\nresource: db-prod-01",
  "decide": {
    "action": "deny_access",
    "decided_at": 1788799391.641898
  },
  "parse_output": {
    "label": "UNKNOWN"
  },
  "tag_summary": "urgent,oncall,db,prod,incident"
}

identical: False
DIVERGED: parse_output.label and/or decide.decided_at differ between two runs of the SAME input, in code that looks deterministic at a glance.

=== Leak 3: set() iteration order across separate process runs ===
process A tag_summary: prod,urgent,db,incident,oncall
process B tag_summary: prod,oncall,incident,db,urgent
identical across processes: False

=== Contrast: the disciplined pipeline on the SAME input/pressure ===
disciplined deterministic log run1 == run2: True
{
  "assemble_input": "REQUEST\nreason: urgent prod incident\nrequester: alice\nresource: db-prod-01",
  "decide": {
    "action": "grant_access",
    "reason": "model approved request"
  },
  "parse_output": {
    "label": "APPROVE"
  }
}
```

Ghi chú về một lần chạy trước đó (giữ lại ở đây vì nó là bằng chứng quan trọng
nhất trong cả thư mục này, chứ không phải vì nó tái lập được theo ý muốn — câu
chữ chính xác luôn được chọn ngẫu nhiên): ở một lần gọi khác, `decide` đã lật
giữa `deny_access` và `grant_access` với cùng một `user_request`, thuần túy vì
`naive_parse_output` tình cờ khớp một template mở đầu bằng đúng từ "Approve." ở
lần này và "Yes," ở lần kia. Phán quyết nền *thật* (được cài sẵn trong prompt)
không hề đổi — chỉ cách parser ngây thơ đọc nó là đổi:

```
--- run1 'deterministic-looking' log ---
{
  ...
  "decide": { "action": "deny_access", "decided_at": 1788799216.612475 },
  "parse_output": { "label": "UNKNOWN" },
  ...
}

--- run2 'deterministic-looking' log ---
{
  ...
  "decide": { "action": "grant_access", "decided_at": 1788799216.612482 },
  "parse_output": { "label": "APPROVE" },
  ...
}
```

Đây không phải một khác biệt log mang tính hình thức — đây là một quyết định
access-control âm thầm lật ngược tùy theo model tình cờ chọn cách diễn đạt nào.

---

## 3. Record/replay — cả pipeline trở nên tái lập được

Minh họa: ghi lại lời gọi bất định duy nhất tại ranh giới vào một file fixture,
rồi phát lại `run_pipeline()` từ fixture đó thay vì gọi thật. *Toàn bộ* log — kể
cả phần `nd` — giờ giống nhau từng byte qua các lần chạy.

```
$ python3 record_replay.py record
Recorded boundary output to fixtures/boundary_output.json:
{
  "latency_ms": 311,
  "raw_confidence": 0.959,
  "raw_text": "Approved. This satisfies the policy requirements."
}

$ python3 record_replay.py replay
=== Replayed run 1 (full log: deterministic + nd) ===
{
  "deterministic": {
    "assemble_input": "REQUEST\nreason: urgent prod incident\nrequester: alice\nresource: db-prod-01",
    "decide": {
      "action": "grant_access",
      "reason": "model approved request"
    },
    "parse_output": {
      "label": "APPROVE"
    }
  },
  "nd": {
    "boundary_call": {
      "latency_ms": 311,
      "raw_confidence": 0.959,
      "raw_text": "Approved. This satisfies the policy requirements."
    }
  }
}

=== Replayed run 2 (full log: deterministic + nd) ===
{
  "deterministic": {
    "assemble_input": "REQUEST\nreason: urgent prod incident\nrequester: alice\nresource: db-prod-01",
    "decide": {
      "action": "grant_access",
      "reason": "model approved request"
    },
    "parse_output": {
      "label": "APPROVE"
    }
  },
  "nd": {
    "boundary_call": {
      "latency_ms": 311,
      "raw_confidence": 0.959,
      "raw_text": "Approved. This satisfies the policy requirements."
    }
  }
}

full pipeline byte-identical across replayed runs: True
```

---

## 4. Nhánh tùy chọn `--live` suy giảm an toàn khi chưa cấu hình key

Minh họa: `run_stable.py --live` thử gọi OpenRouter thật (chỉ khi được bật), và
lùi về stub offline kèm một cảnh báo rõ ràng — không bao giờ crash, không bao giờ
in key ra — khi `OPENROUTER_API_KEY` không có trong môi trường shell. Bản chứng
minh này không bao giờ phụ thuộc vào kết nối mạng.

```
$ env | grep -c OPENROUTER_API_KEY
0
$ python3 run_stable.py --live
WARNING: live LLM call failed (RuntimeError); falling back to stub
WARNING: live LLM call failed (RuntimeError); falling back to stub
=== Run 1: deterministic log ===
{
  "assemble_input": "REQUEST\nreason: urgent prod incident\nrequester: alice\nresource: db-prod-01",
  "decide": {
    "action": "grant_access",
    "reason": "model approved request"
  },
  "parse_output": {
    "label": "APPROVE"
  }
}
...
=== Summary ===
deterministic logs byte-identical: True
non-deterministic logs byte-identical: False
```

(Output đầy đủ có hình dạng y hệt Mục 1 — cờ `--live` chỉ đổi xem hàm nào lấp
vào contract của ranh giới; phần còn lại của pipeline không biết và cũng không quan tâm.)

---

## 5. Kiểm tra render diagram (Playwright)

`diagram.mmd` đã được render qua harness mermaid cục bộ của repo
(`experiments/agent-infra/_diagram-harness/render.mjs` + `mermaid.min.js` đã
vendor) và mở trong một phiên Chromium headless bằng các tool Playwright MCP.
`window.__harness.status` báo `"ok"` không có lỗi console nào, và ảnh chụp
(`diagram.png` trong thư mục này) đã được đối chiếu bằng mắt với code: input đi
vào `assemble_input`, vào ranh giới bất định màu hồng, rồi vào `parse_output` →
`decide`, với phần tách log `nd` và log deterministic cùng fixture record/replay
đều hiện ra dưới dạng các nhánh phụ nét đứt.
