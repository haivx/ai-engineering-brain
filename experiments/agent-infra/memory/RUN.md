# RUN.md — cross-run session state vs. durable log proof

Environment: Python 3.9.6, standard library only. Run from
`experiments/agent-infra/memory/` (or the repo root — paths in `run.py` are
anchored to the script's own directory). `SESSION_MAX_RUNS = 2`, so 3
separate invocations are enough to see a session accumulate, expire, and
get replaced.

Each `python3 run.py run` below is a **separate process invocation** — this
is deliberately a cross-run proof, not a cross-step proof like `state/`.

All output below is copied verbatim from actual terminal runs of `run.py`.

---

## Run #1 — fresh session created

Demonstrates: with no `session.json` on disk, a new session (`S1`) is
created; its id is derived deterministically from how many
`session_start` events already exist in `log.jsonl` (zero, here), not from
a wall clock. Both tiers are updated: `log.jsonl` gets an append, and
`session.json` is written fresh.

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

## Run #2 — session continues, then hits its lifetime limit and expires

Demonstrates: the second invocation picks up `session.json` and continues
`S1` (`run_count` 1 -> 2). Reaching `SESSION_MAX_RUNS` on this same run
triggers **promotion**: a `session_summary` record carrying all of `S1`'s
accumulated facts is appended to the durable log, and only then is
`session.json` deleted. The session's state is not silently lost — it is
folded into the permanent record before the ephemeral copy goes away.

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

## Run #3 — a brand new session starts; durable log now spans both sessions

Demonstrates the cross-run accumulation claim: with `session.json` gone, the
third invocation starts a fresh session (`S2` — derived from the fact that
`log.jsonl` now contains one prior `session_start` event). `S1`'s history
is untouched inside `log.jsonl`; `S2`'s new events are simply appended
after it. The durable log now contains the full, ordered history of both
sessions across all 3 runs; `session.json` reflects only the live session.

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

## Reproducibility check

Demonstrates: `reset` followed by the same 3-run sequence produces
byte-identical output every time — session ids and facts are derived only
from prior log content, never from wall-clock time or randomness.

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

Generated files (`session.json`, `log.jsonl`) are build artifacts of
running the demo — they are removed by `python3 run.py reset` and are not
meant to be committed as fixed evidence; the transcripts above are the
durable record.
