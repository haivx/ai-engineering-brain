# NOTES.md — what the run actually showed

- **A checkpoint only proves a step is "done" once its output is
  atomically committed.** `pipeline.py` never appends a step name to
  `checkpoint.json` until after `os.replace()` succeeds for that step. This
  means the checkpoint and the on-disk artifact it describes can never
  disagree — there is no window where the checkpoint says "transform done"
  but the real `step3_transformed.json` is missing or partial.

- **The real answer to "what happens to a half-done step" is: nothing
  happens to it, because it never touches the real path.** `step_transform`
  writes to `step3_transformed.json.tmp.<pid>` and only renames it into
  place at the end. A `SIGKILL` landing in between (which is what run.sh
  actually does — see RUN.md section 2) leaves an orphaned temp file and
  nothing else. The step is safe to just re-run from scratch on restart,
  because it's a pure function of its already-committed input
  (`step2_validated.json`), which the crash never touched.

- **Idempotent-by-recompute turned out to be simpler than any kind of
  "resume mid-step" logic.** I didn't need to track partial progress inside
  a step (e.g. "which array elements were already transformed") — cheap
  steps can just always restart at their own beginning. That only works
  because each step is small, deterministic, and reads a stable input file;
  it would not work as-is for a step with an expensive or non-idempotent
  side effect (e.g. "send an email", "charge a card") — that class needs a
  different answer (dedup keys, a "did I already send this" record), which
  this experiment doesn't cover.

- **The orphaned temp file is genuinely harmless, but only because nothing
  ever reads `*.tmp.*` paths.** `pipeline.py` cleans them up on startup as
  tidiness, not correctness — I proved this by noting the log line "removing;
  the real output was never renamed to it, so nothing referenced it." If a
  future step ever globbed the data directory instead of reading a named
  path, this guarantee would break.

- **Cleanup-of-orphans turned out to be a checkpointing side effect, not a
  given.** `pipeline.py` deletes stale `.tmp.*` files on every startup;
  `no_checkpoint_pipeline.py` has no such logic at all, since it has no
  concept of "startup" beyond "run everything." A crash mid-`transform` in
  the no-checkpoint baseline leaves its orphaned temp file sitting in `data/`
  forever — confirmed directly (`data/step3_transformed.json.tmp.42704`
  during a second full test pass, see RUN.md section 5). It's not just that
  the no-checkpoint baseline redoes work; it also litters uncommitted debris
  that nothing in that design ever revisits. That was not something I set
  out to demonstrate — it fell out of using the same crash-injection
  mechanism against both scripts.

- **Checkpoint granularity is per-step, not per-record.** The pipeline
  redid the entire `transform` step from scratch rather than resuming from
  wherever it got to inside that step. That's the right tradeoff for a
  5-step, sub-second pipeline; a longer-running or more expensive step would
  need finer-grained checkpoints inside itself (or the step should be split
  into smaller sub-steps) to avoid redoing expensive work.

- **The no-checkpoint contrast made the cost concrete rather than
  hypothetical.** Same crash, same step, same 5 steps — but `run4.log` shows
  `fetch_input` and `validate` both re-running after the restart, work the
  checkpointed version explicitly skipped (`run2.log`: two `SKIP` lines).
  For 5 cheap steps this is a rounding error; the point generalizes badly
  once any of the skipped steps is slow or has an external side effect
  (an API call, a charge) that a checkpoint would have prevented from
  happening twice.

- **The "resumed run == uninterrupted run" equality check is the strongest
  evidence in this experiment**, not the log narration. `RUN.md` section 4
  shows both runs' final `step5_report.json` hashing to the identical md5
  (`a2d801bf...`). A resumed run isn't just "close enough" — for this
  pipeline (pure, deterministic steps) it is byte-for-byte the same
  artifact a never-interrupted run would have produced.

- **Non-atomic writes turn a recoverable failure into an unrecoverable
  one.** `unsafe_step_demo.py` is the same kind of kill, but because it
  writes directly to the real path in two chunks, the resulting
  `unsafe_output.json` is permanently truncated invalid JSON — and nothing
  about restarting fixes it, because there is no checkpoint concept telling
  anyone that file is bad. This was the most useful negative result: it
  shows atomicity and checkpointing are two separate mechanisms that both
  have to be right — a checkpoint that points at a corrupted file is
  useless.

- **Surprise: I didn't need `try/except` anywhere for the crash path.** The
  crash is a real `SIGKILL`, which Python cannot catch or run cleanup code
  for. That's exactly why the atomic-write + checkpoint-after-commit design
  matters — it has to survive a failure mode where the crashing process gets
  zero chance to react, not just a `try/except`-able exception. (The
  `sys.exit(99)` "safety timeout" path in `maybe_crash()` *is* a normal
  exception-like exit, but it only ever fires if the driver fails to deliver
  the kill in time — it did not fire in either captured run.)

- **What this experiment does not prove**: concurrent/parallel step
  execution, checkpointing partway through a single expensive step, crash
  recovery for non-idempotent side effects (network calls, payments), or
  checkpoint-store corruption itself (what if the kill lands during the
  checkpoint's own `os.replace`? — not exercised here, though the same
  atomic-write mechanism is used for `checkpoint.json` too, so the argument
  should extend, but I did not force a kill at that exact instant to check).

See [[recovery]] concept file and `experiments/agent-infra/recovery/RUN.md`
/ `diagram.mmd` for the evidence this is distilled from.
