# Playbook: building a minimal eval set

Goal: compare the same task across multiple models, graded automatically, no gut feeling.

## Steps
1. Collect 15–30 cases representative of what you ACTUALLY do (input + a "pass" criterion defined up front).
2. One cases file (json/yaml). Each case: prompt + how to check the result.
3. One loop: for each model string, call it through LiteLLM with the same prompts and collect the outputs.
4. Grade automatically, by type:
   - Code → run the tests, count the pass rate.
   - Structured output → validate with Pydantic, count the parse pass rate.
   - Tool-calling → compare against the expected tool/arguments.
   - Subjective → LLM-as-judge (rubric or A/B pairwise); remember the judge's score is only a signal.
5. Print a comparison table: model × (pass rate, price, speed).
6. Save the results to experiments/ — this is YOUR real data, not something you can Google.
7. Log every case as structured JSONL records, not print statements — one line per pipeline step, not per case. Fields: `run_id`, `case_id` (together make a failure greppable back to its trace), `step`, `status` (`ok`/`error` — never fold "wrong answer" and "crashed" into one bucket), `duration_ms`, `error`.
8. Give each pipeline stage its own record — a case-level "failed" can't tell you which stage crashed.
9. Save each run's result summary to a tagged file (`results/eval_<tag>.json`) — you need last run's numbers on disk, not in scrollback.

## Principle
- Measure, don't guess. A prior from public benchmarks is no substitute for an eval on your real task.
- When testing a change, diff the per-case flip list between two saved results, not just the headline delta — a net "+X%" can hide N cases newly passing offset by M newly failing.
- Zero flips before/after means the eval doesn't exercise that variable — fix the cases, don't report the null result as "no regression."
- A pass-rate number says how much is broken; the structured log says which case and why. Keep both.
