# RUN.md — single-run working state proof

Environment: Python 3.9.6, standard library only. Run from
`experiments/agent-infra/state/` (or the repo root — paths in `run.py` are
anchored to the script's own directory).

All output below is copied verbatim from actual terminal runs of `run.py`.

---

## 1. Normal run: two tiers, written to two separate files

Demonstrates: `working.json` is overwritten every step (pure scratch, no
memory of its own history); `log.jsonl` is appended to every step (durable,
never rewritten). After the run, `working.json` reflects only the final
state (nothing to prove there), while `log.jsonl` holds one line per step.

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

## 2. Forced crash + wipe of working state + reconstruction from the durable log

Demonstrates the core boundary claim: a run (`R2`) is crashed on purpose
after step 3 (`--crash-at 3`), leaving `working.json` dangling with
in-progress scratch data. `working.json` is then deleted outright
(`wipe-working`, simulating a process death / container recycle). The run's
progress is then fully reconstructed using **only** `log.jsonl` — proving
that wiping the ephemeral tier loses nothing that was already committed.

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

## 3. The inverse mistake: single-blob design loses history on the same wipe

Demonstrates what the tier separation is actually preventing. `blob-run`
merges scratch state AND full history into **one** file (`blob.json`),
overwritten every step — the design many "just store it in a file" systems
default to. It is crashed at the identical point (step 3) and wiped the
same way. Because there was never a separate append-only store, the wipe
destroys all 3 already-completed step results, not just the in-flight one.

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

## 4. Reproducibility check

Demonstrates: the whole proof is deterministic — `reset` then the same
command sequence produces byte-identical output, every time, from a clean
slate (no wall-clock timestamps or randomness anywhere in `run.py`).

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

Generated files (`working.json`, `log.jsonl`, `blob.json`) are build
artifacts of running the demo — they are removed by `python3 run.py reset`
and are not meant to be committed as fixed evidence; the transcripts above
are the durable record.
