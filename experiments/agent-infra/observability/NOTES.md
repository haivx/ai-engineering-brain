# NOTES.md — what the run actually showed

- The pass-rate number and the structured log answer different questions,
  and you need both. `12/18` (66.7%) tells you *how much* is broken;
  grepping `logs/run_baseline.jsonl` by `case_id` tells you *which* case,
  *which pipeline step*, and *why* in one command. `naive_baseline_demo.py`
  reaches the identical 12/18 with zero structure and cannot answer any of
  those follow-ups — see RUN.md §5.

- Changing one variable (`--threshold` 0.0 -> 0.2) moved the pass rate by
  a real, non-zero amount (+11.1 points) and did so through explainable
  per-case flips, not noise. `compare_runs.py` renders those flips
  directly from `results/eval_*.json` — no re-reading of the JSONL log was
  needed to get the before/after verdict, only to get the *root cause*.

- The threshold change was not a pure win. It fixed 5 false positives
  (off-topic text incidentally matching one keyword) but broke 3 true
  positives (genuine tickets whose only signal was one keyword). A single
  pass-rate number would have shown "+11.1%" and hidden that trade-off
  entirely; the per-case diff in `compare_runs.py` is what surfaces it.
  Surprise: it would have been easy to report only the headline number and
  call the change strictly better, which it isn't.

- Distinguishing "the pipeline ran and produced a wrong answer" from "the
  pipeline crashed" required a `status` field (`ok` vs `error`) at the
  step level, not just at the case level. Both look identical from a bare
  pass/fail count. This is the single field that made the localized-failure
  argument in RUN.md §5 possible.

- `step_seq` plus `step` name (not just "an error occurred") let me see
  the crash happened in `normalize`, at step 1 of 5 — before `tokenize`,
  `score`, or `decide` ever ran. Without a per-step record, "it failed"
  gives no information about which stage of a 4-stage pipeline never even
  started.

- No seeding was actually needed for a stable pass rate: this system has
  zero randomness in its decision logic (pure keyword counting), so two
  runs of the same threshold produce bit-for-bit identical `pass_rate`
  values (verified in RUN.md §4). The "seed your non-determinism"
  requirement turned out to be satisfiable by having none in the scored
  path — worth noting because a more realistic system (LLM-in-the-loop)
  would not get this for free and would need explicit seeding or mocking
  to get the same reproducibility.

- `run_id` (a `uuid4`) is intentionally NOT seeded and differs every run.
  That's fine — it's a correlation key, not part of the scored logic. It's
  a useful reminder that "make it deterministic" only needs to apply to
  the fields the eval score depends on, not to every field in the log.

- Truncating logged input/output (`_truncate`, 200 chars) mattered in
  practice: the `case_result` record embeds a full outcome dict as its
  `output` field, and without truncation a handful of verbose cases would
  make the JSONL harder to skim by eye. This is a real operational
  concern, not a hypothetical one — it showed up in the actual log output
  (see the `<truncated>` marker in RUN.md §5b).

- The eval harness treats "errored" as a strict subset of "failed" for
  scoring (an error always fails the case) but logs it as a distinct
  status. Two different failure *rates* (misclassification vs. crash) are
  worth tracking separately even though only one number ("passed") is the
  headline metric — the summary record keeps both (`failed` and `errored`
  are separate counters, not merged).

Evidence backing every point above: `experiments/agent-infra/observability/`
(`router.py`, `eval_harness.py`, `compare_runs.py`, `naive_baseline_demo.py`,
`eval_cases.json`, `logs/`, `results/`, `RUN.md`).
