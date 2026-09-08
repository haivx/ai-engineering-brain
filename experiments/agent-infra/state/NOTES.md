# NOTES.md — state/ (single-run working state)

- Separating `working.json` (overwritten) from `log.jsonl` (append-only) cost
  nothing extra in the code — the log write is one extra line per step. The
  discipline is cheap; it's the *habit* of doing it that's the actual
  practice, not the mechanism.
- The proof only works because "durable" was defined narrowly and honestly:
  append-only, one file, never truncated, never rewritten. The moment a
  "durable" store also gets `overwrite`d (like the blob anti-pattern does),
  it stops being durable in practice even if you call it that.
- The reconstruction step (`reconstruct`) is doing real work: it's not just
  "the log still has the data," it's "you can derive the correct resume
  point (step 4) purely from what's committed," which is the actual
  operational payoff, not just "no data loss" in the abstract.
- The anti-pattern (`blob.json`) was the more instructive half of this
  exercise. It's not a strawman — it's the natural first draft anyone
  writes ("just dump my state to one JSON file"), and it fails silently:
  nothing looks wrong until the exact moment of a crash + cleanup.
- Surprise: the blob design's `history` field, while it existed, actually
  looked *better* than the separated design mid-run (it visibly carries
  more information right there in one file). The failure is invisible until
  the wipe happens — this is worth stressing in the concept paragraph,
  since "looks fine most of the time" is exactly why the mistake persists.
- Determinism required removing all wall-clock/random elements — `step *
  step` as the "computation" stands in for a real deterministic
  transform. In a real agent run, the working-state tier would hold things
  like partial LLM output buffers or tool-call scratch args; the log would
  hold only the committed result of each completed step, same shape as here.
- What this experiment does NOT prove: it doesn't show automatic *recovery*
  (resuming execution from step 4 and finishing steps 4-5) — only that the
  information needed to do so survives the wipe. Actual resume-from-checkpoint
  behavior belongs to `experiments/agent-infra/recovery/`, not here — this
  folder proves the data survives, not that a process automatically picks
  it back up.
- One-file-per-tier is a real constraint worth keeping: at no point did the
  script need to know the schema of the *other* tier's file to do its job,
  which is what makes wiping one of them in isolation both safe (for the
  log) and legible as a failure (for the blob).
