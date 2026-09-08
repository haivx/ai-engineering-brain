# RUN.md — checkpoint / resume across a real process restart

This is the actual captured stdout of `./run.sh` (Python 3.9.6, macOS, stdlib
only), run from a clean state. Nothing below is invented — it is copied
verbatim from a real terminal session. `run.sh` launches `pipeline.py` as a
genuine subprocess and kills it with a real `SIGKILL` (`kill -9`) from the
driver, not a simulated failure inside one continuous run; every "restart"
below is a brand new Python process with no shared memory.

The 5-step pipeline (`steps.py`): `fetch_input -> validate -> transform ->
aggregate -> write_report`. Each step commits its output atomically (write to
a temp file, `os.fsync`, then `os.replace` to the real path) and
`pipeline.py` appends the step's name to `checkpoint.json` (also written
atomically) only after that commit succeeds.

---

## 1. Uninterrupted happy-path run (the baseline we compare against)

Demonstrates: a clean, uninterrupted run of all 5 steps, producing the
reference final report and its md5.

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

## 2. Real crash: SIGKILL sent to the process mid `transform` step

Demonstrates: an actual external `kill -9` (exit status 137, the standard
"killed by SIGKILL" code) landing after the step's side effect (a temp file)
is on disk but *before* the atomic rename that would commit it and *before*
any checkpoint for `transform` is written. This is the half-done-step case.

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

(The process never gets to log anything further — the next line in the
source, `os.replace(tmp_path, out_path)`, never ran. This is the real
`SIGKILL`, not a caught exception: nothing in `pipeline.py` handles it or
gets a chance to clean up.)

### On-disk state after the kill, before any restart

Demonstrates: what a half-done step actually leaves behind — the checkpoint
still only lists the two steps that *fully* committed, and the crashed
step's side effect survives on disk as an orphaned, uncommitted temp file.

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

## 3. Restart: a brand-new process resumes from the last checkpoint

Demonstrates: this is a fresh `python3 pipeline.py` invocation (new PID) with
no shared memory with the killed one. It reads `checkpoint.json` off disk,
discards the orphaned temp file from the half-done step (idempotent
re-derivation is the answer here, see NOTES.md), **skips** `fetch_input` and
`validate` (not redone), and re-runs `transform` from scratch through to
completion.

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

## 4. Equality check: resumed result vs. uninterrupted happy-path result

Demonstrates: the whole point of checkpointing — the crash-and-resume run
produces a byte-identical final artifact to the never-interrupted run, even
though it took a real kill in the middle.

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

## 5. Contrast: no-checkpoint baseline restarts from zero

Demonstrates: the same crash injected into `no_checkpoint_pipeline.py` (same
5 steps, same crash point, but it never reads or writes a checkpoint). The
first process dies the same way (SIGKILL, exit 137) after `fetch_input` and
`validate` have already run. On restart, since there is no record of what
happened, **`fetch_input` and `validate` run again** — the exact waste
checkpointing exists to eliminate.

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

**Undocumented-until-now side effect worth calling out**: the SIGKILL above landed after `no_checkpoint_pipeline.py` had already written `data/step3_transformed.json.tmp.<pid>` (same temp-file mechanic as `steps.py` uses everywhere). Because `no_checkpoint_pipeline.py` has no startup cleanup step (unlike `pipeline.py`, which globs and deletes `data/*.tmp.*` on every launch — see section 3's `clean_orphaned_temp_files`), that orphaned temp file is never removed by anything in this design. `run4` below creates its own new temp file for `transform` and commits normally, but the stray file from `run3`'s crash is left sitting in `data/` indefinitely — across every future crash of this baseline, the litter would only grow. This was observed directly during a second full `./run.sh` pass (`data/step3_transformed.json.tmp.42704`, flagged during review) and is genuine crash residue, not a bug in the harness. It does not appear in the final resting `data/` snapshot committed alongside this file, because that snapshot was produced by a later, separate `pipeline.py` crash+resume cycle whose `rm -rf data` reset wiped it — see "On-disk resting state" at the bottom of this file.

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

## 6. Cost of a non-atomic step (same kind of kill, no temp+rename)

Demonstrates: `pipeline.py`'s answer to "what happens to a half-done step" is
atomic commit (temp file + `os.replace`). `unsafe_step_demo.py` shows the
alternative: writing directly to the real output path in two chunks. The
same kind of external `SIGKILL`, landing between the two chunks, leaves the
**real** file permanently corrupted — there is no orphaned temp file to
discard here, the damage lands exactly on the artifact that matters.

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

## Reproducibility

The full sequence above was re-run a second time from a clean slate
(`./run.sh`) and produced the identical outcome at every checkpoint: same
skip pattern, same `RESULT: MATCH` at step 7, same corruption at step 9
(PIDs differ between runs, everything else is deterministic). It was that
second pass that produced the orphaned `no_checkpoint_pipeline.py` temp file
discussed in section 5 above.

---

## On-disk resting state (what's actually sitting in this folder right now)

`checkpoint.json` and `data/*.json` at rest reflect a **fully completed,
already-resumed** pipeline: `checkpoint.json` lists all 5 steps, and `data/`
holds only the 5 final committed outputs — no `*.tmp.*` files, because they
were produced by one more crash+resume cycle run explicitly to leave a clean
final snapshot, and `pipeline.py`'s startup step deletes orphaned temp files
on the very next launch (that's the "removing; the real output was never
renamed to it" log line in section 3 above). The mid-crash, orphan-present
disk state is preserved only in this file's transcripts (section 2's `ls -la`
output) and in `run1.log`/`run2.log` — not as a standing artifact, because
nothing in `pipeline.py`'s design is meant to preserve it past the next run.

Two related facts worth being explicit about, since they read differently
depending on which script you're looking at:

- **`pipeline.py` actively cleans stale `.tmp.*` files on every startup** —
  it doesn't merely ignore them. This is deliberate tidiness, not a
  correctness requirement (nothing ever reads those paths either way).
- **`no_checkpoint_pipeline.py` has no such cleanup and never will** — any
  temp file it orphans via a mid-`transform` crash sits in `data/`
  permanently, accumulating across repeated crashes. See section 5 above for
  the directly observed instance of this.
- **`crash_trigger`** (repo root) is a live, driver-only IPC file: the
  crashing child touches it to tell `run.sh` "a side effect has started, kill
  me now," and each phase in `run.sh` removes it before creating it fresh.
  It has no meaning once `run.sh` exits, so a final cleanup line was added at
  the end of the driver to remove it rather than leave unexplained signaling
  residue on disk after a full run completes.
