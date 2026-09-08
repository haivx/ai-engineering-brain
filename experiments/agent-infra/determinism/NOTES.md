# NOTES.md — what the runs actually showed

For the Concepts Editor writing `concepts/agent-infra/determinism.md`.
See `RUN.md` for the captured output these bullets are drawn from.

- The core claim held exactly as stated: isolating the non-deterministic
  call behind one function with a fixed input/output contract (`boundary.py:
  non_deterministic_call`) let everything else (`assemble_input`,
  `parse_output`, `decide`) produce byte-identical JSON logs across two
  runs of the same input, every time, while the boundary's own output
  (wording, confidence, latency) varied every time. No exceptions across
  ~10 runs.

- The most useful result wasn't the stable run — it was the leak demo.
  On one invocation of `leak_demo.py`, the naive-parse leak actually
  **flipped the access-control decision** (`grant_access` vs `deny_access`)
  for the identical input, purely because the model's phrasing happened to
  start with a different word ("Approve." vs "Yes,"). The ground-truth
  verdict never changed. This is a much stronger argument than "the logs
  look different" — a leaked-non-determinism bug in the parsing layer can
  silently change what the system *does*, not just what it *logs*.

- Confirms a subtlety worth stating precisely in the concept: "deterministic
  outside the boundary" does not mean "the same answer every time" — the
  disciplined pipeline's final decision can legitimately vary if the
  boundary's semantic content varies. What must stay stable is the
  *process*: given the same boundary output, the surrounding code always
  does the same thing. The stub was deliberately built so the label is
  recoverable regardless of phrasing, which is what makes "same decision
  both runs" a meaningful proof rather than a coincidence of the stub.

- The `set()`-iteration leak needed a genuinely separate observation
  method: within one running process, a set's iteration order does NOT
  reshuffle between two calls — it only varies **across separate `python3`
  process invocations** (CPython's per-process string-hash randomization).
  I had to shell out to `subprocess` to actually demonstrate this one; the
  in-process two-calls pattern used for the other leaks would have shown
  "identical" and hidden the bug. Worth a line in the concept: some
  non-determinism only shows up in prod (many process restarts), not in a
  dev loop that calls a function twice in one process.

- The wall-clock-timestamp leak was the most trivial to introduce and the
  most obviously bad in hindsight — one line (`"decided_at": time.time()`)
  inside code that otherwise looked like pure decision logic. It's a good
  concrete example of "hidden randomness" that has nothing to do with an
  LLM at all; determinism-at-the-boundary discipline is a general
  data-flow property, not an LLM-specific concern.

- Record/replay (the bonus) worked with almost no extra code: because
  `run_pipeline()` already took `boundary_fn` as a parameter (needed for
  the `--live` opt-in path anyway), plugging in a fixture-reading closure
  made the *entire* log — including the previously-varying `nd` section —
  byte-identical across runs. The practical payoff described in PLAN.md
  §6 is real and cheap once the boundary is a real function argument
  rather than a hardcoded call.

- Surprise / thing that didn't go as expected: I initially assumed the
  non-deterministic (`nd`) logs would visibly differ on literally every
  pair of runs, and wrote `run_stable.py` to treat that as an expected
  fact. With only 4 templates × a continuous confidence float × a random
  latency int, in practice they always did differ across the sampled runs
  — but the confidence/latency alone make a repeat close to impossible,
  not strictly impossible (a coincidental identical draw is technically
  possible with 4 templates and a narrow uniform range). `run_stable.py`
  handles this as a note rather than a failure so the script's exit
  status doesn't depend on it.

- What I could NOT prove: real-world LLM sampling variance itself. The
  `--live` path exists and is wired to the same boundary contract
  (`live_llm_call` in `boundary.py`), and degrades safely (no crash, no
  printed key) when `OPENROUTER_API_KEY` isn't set — see RUN.md §4 — but
  I did not exercise it against the live OpenRouter API, per the
  instruction to keep the proof network-independent by default. The stub's
  "same label, different wording" behavior is a deliberate simplification,
  not a measured property of any real model.

- Scope note: this proof is about STRUCTURE (one function boundary, pure
  code around it, explicit split between the two log halves), not about
  making the non-deterministic output itself "more deterministic" (e.g.
  temperature=0, seeding). Those are complementary techniques the concept
  paragraph could mention as adjacent but distinct — they reduce *how much*
  the boundary varies; the boundary discipline here is about containing
  variance that exists, however much of it there is.
