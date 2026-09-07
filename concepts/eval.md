# Eval

To know whether a model is "good enough" for your work → measure it, don't guess.

## Pitfall: public benchmarks
"Model X matches o4-mini on MMLU" gives only a rough *prior* (the model isn't junk).
It does NOT answer: "is this model good enough for MY task?"
Benchmarks measure generic problems; your eval has to measure your actual task.

## How to do it: a small eval set drawn from your own task
15–30 cases representative of what you usually do is enough to see the differences.
For each case, define what "pass" means BEFORE running it.
The infrastructure is already there: LiteLLM keeps the messages identical, you only change the `model` string → run the same prompts across many models.

## For coding/agents, "quality" = what RUNS, not what feels good
Grade automatically with code — that's the only thing that scales:
- **Does the code run / pass the tests?** — binary, not arguable. Generate code → run pytest → count the pass rate.
- **Does the structured output match the schema?** — does Pydantic's `model_validate_json()` pass or fail? Count the ratio.
- **Is the tool-calling correct?** — right tool, right arguments, right order? This is where cheap models fail most.
- **Instruction-following?** — tell it "JSON only, no preamble": does it listen?

## Subjective tasks (writing, explanation) → LLM-as-judge
Hand the output to a strong model to grade against a rubric, or do A/B pairwise comparison.
Bias warning: judges favor long answers and favor output from their own model family. The judge's score is only a signal, not the truth.

## Realistic expectations
- Extraction / classification / fixed formatting → cheap models are usually ON PAR with frontier ones; use them.
- Multi-step reasoning / long agent loops → frontier models pull far ahead (compounding error).
