# RUN.md — captured terminal output

Environment: Python 3.9.6, stdlib only, run from this directory with
`python3 <script>.py`. All output below is copy-pasted from real runs, not
invented.

---

## 1. Disciplined boundary — deterministic logs stay byte-identical

Demonstrates: same input run twice through `boundary.run_pipeline()`. The
`nd` (non-deterministic boundary) log differs every run; the `deterministic`
log (input assembly, parsing, decision) is byte-identical, with an explicit
diff proving it.

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

## 2. Leaked non-determinism — the failure mode, then the contrast

Demonstrates three ways non-determinism sneaks past a boundary into code
that looks deterministic (naive parsing keyed on incidental phrasing;
a wall-clock timestamp stamped into a decision record; `set()` iteration
order across process invocations), then re-runs the disciplined pipeline
on identical input/pressure for direct contrast.

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

Note on an earlier run (kept here because it is the most important evidence
in this whole folder, not because it's reproducible on demand — the exact
words are only ever chosen by chance): on a different invocation, `decide`
flipped between `deny_access` and `grant_access` for the identical
`user_request`, purely because `naive_parse_output` happened to match a
template starting with the literal word "Approve." on one run and "Yes,"
on the other. The *real* underlying verdict (baked into the prompt) never
changed — only the naive parser's read of it did:

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

This is not a cosmetic log difference — it is an access-control decision
that silently flips depending on which phrasing the model happened to pick.

---

## 3. Record/replay — the whole pipeline becomes reproducible

Demonstrates: capture the boundary's one non-deterministic call to a fixture
file, then replay `run_pipeline()` from that fixture instead of a live call.
The *entire* log — including the `nd` section — is now byte-identical
across runs.

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

## 4. Optional `--live` path degrades safely with no key configured

Demonstrates: `run_stable.py --live` attempts a real OpenRouter call (opt-in
only), and falls back to the offline stub with a clear warning — never a
crash, never a printed key — when `OPENROUTER_API_KEY` isn't in the shell
environment. This proof never depends on network access.

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

(Full output identical in shape to Section 1 — the `--live` flag only
changes which function fills the boundary contract; the rest of the
pipeline does not know or care.)

---

## 5. Diagram render check (Playwright)

`diagram.mmd` was rendered via the repo's local mermaid harness
(`experiments/agent-infra/_diagram-harness/render.mjs` + vendored
`mermaid.min.js`) and opened in a headless Chromium session through the
Playwright MCP tools. `window.__harness.status` reported `"ok"` with no
console errors, and the screenshot (`diagram.png` in this folder) was
visually checked against the code: input to `assemble_input`, into the
pink non-deterministic boundary, into `parse_output` → `decide`, with the
`nd` vs deterministic log split and the record/replay fixture both shown
as dashed side paths.
