# Feed for playbooks/build-eval-set.md

Additions learned from building `experiments/agent-infra/observability/`.
Written in the playbook's terse numbered-step voice. The Concepts Editor
should merge these in — not restating steps 1-6 or the Principle already
there.

## Additions to the "Steps" list (structured logging, not print statements)

7. Log every case as structured records (JSONL), not print statements —
   one JSON object per line, one line per step. Each record needs at
   least: `run_id` (shared by every record in one invocation of the
   harness), `case_id` (shared by every record for one test case),
   `step` (which stage produced this record), `status` (`ok` / `error` —
   never fold "wrong answer" and "crashed" into the same bucket),
   `duration_ms`, and `error` (`null` unless `status` is `error`).
   `run_id` + `case_id` together are what let you `grep` one failure back
   to its full step-by-step trace instead of re-running with prints added.

8. Give every pipeline stage its own record, not just a final
   pass/fail per case. A case with 4 internal steps that crashes on step 1
   should show `step: "<stage_name>"` at the point of failure — a single
   "case failed" record can't tell you whether the crash happened before
   or after the model was even called.

9. Before changing anything, save the eval's result summary to a file
   keyed by a short tag (`results/eval_<tag>.json`), not just to stdout.
   You need last run's numbers on disk to diff against, not in scrollback.

## Addition to the "Principle" section (before/after comparison discipline)

- When testing whether a change (threshold, prompt, model swap) helped,
  change exactly one variable between two runs and diff the saved result
  files, not just the two pass-rate headlines. A single "+X%" number can
  hide a wash — e.g. N cases newly passing and M different cases newly
  failing. Report both the net delta and the per-case flip list (which
  case, which direction, old answer vs new answer) so "did this help"
  and "what did it trade away" are both answered from the same table.
- Verify the eval is actually sensitive to the variable you're testing
  before trusting a comparison: if before/after produces zero flips, the
  eval set doesn't exercise that variable and the comparison proves
  nothing — fix the cases, don't report the null result as "no
  regression."
- A pass-rate number and a structured log answer different questions:
  the number says how much is broken, the log says which case and why.
  Keep both — a bare aggregate score with no per-case, per-step trace
  behind it is not enough to debug a regression, only to notice one.
