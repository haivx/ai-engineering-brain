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

## Principle
Measure, don't guess. A prior from public benchmarks is no substitute for an eval on your real task.
