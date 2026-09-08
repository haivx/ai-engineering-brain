# Agent Infra

Mental models for the infra layer underneath an agent — state, memory,
determinism, observability, resumability — each distilled only from a
proven experiment in the matching `experiments/agent-infra/<topic>/`
folder, per this repo's proof-before-prose rule.

## What's here

- `state.md` — working state, single run. Dies at run end; separate
  disposable scratch from an append-only durable log so a crash never
  loses committed progress.
- `memory.md` — state across runs (a session), between `state.md`'s scope
  and the permanent durable log. Session state has a bounded lifetime and
  must be promoted into the durable log before deletion, or it repeats
  `state.md`'s failure one level up.
- `determinism.md` — isolating a non-deterministic call behind one
  function boundary so everything around it stays reproducible, and what
  happens when that isolation leaks.
- `observability.md` — the structured trace underneath an eval's headline
  number. Owns tracing/instrumentation only; eval methodology lives in
  `concepts/eval.md`, and the eval-harness half feeds
  `playbooks/build-eval-set.md`.
- `recovery.md` — checkpoint-and-resume across a real process restart: a
  checkpoint is only trustworthy paired with atomic commits.

`state.md` and `memory.md` are deliberately separate: "what dies at the
end of one run" versus "what persists across runs, and for how long."
Neither covers the other's scope.

## Still opening framing only (no experiment yet)

These came from the cluster scaffold and remain short framing paragraphs.
Per this repo's proof-before-prose rule, each gets a deep dive only once
an experiment lands in `experiments/agent-infra/<topic>/` — not before:

- `context-engineering.md` — what goes into context each step
- `tool-calling.md` — the model to world interface
- `orchestration.md` — single loop vs multi-agent, sub-agents
- `guardrails.md` — validate before acting

## Wrap-up: which of these would silently break first?

Determinism leaks break first in time — no failure event required. The
determinism experiment showed a naive parser flip a real access-control
decision (grant vs. deny) for the identical input, purely from incidental
phrasing, with no exception raised
(`experiments/agent-infra/determinism/RUN.md`, §2). That can happen on the
first ordinary run of an otherwise healthy system.

The other "state-shaped" patterns need something to go wrong first — a
crash, an expiry, a restart — and differ in how loud the aftermath is:

- State and memory tiering failures are silent but conditional: the
  single-blob anti-pattern looks *better* than the correct design while
  healthy (`state/NOTES.md`), and only reveals the loss at the exact
  moment of a crash-and-wipe. The session-tiering failure in `memory.md`
  is the same shape, gated behind expiry instead of a run crash.
- Recovery failures split in two. Losing checkpointing entirely is *loud*:
  steps visibly re-run in the log (`recovery/RUN.md`, §5). Non-atomic
  writes inside the same experiment are silent: a corrupted file sits on
  disk with nothing to flag it as bad (`recovery/NOTES.md`).

Whether any of this is ever *discovered* is governed by a fifth pattern
that isn't a failure mode of its own: observability. The observability
experiment proves this independently — a structured harness and a naive
print-wrapped version scored the identical 12/18 on the identical 18
cases, and the naive version couldn't tell a crash apart from a wrong
answer (`observability/RUN.md`, §5). A system with no structured trace
shows "a slightly worse score" for a genuine regression and a code-level
crash, indistinguishably — and the same experiment shows a bare headline
can hide a real trade-off even when nothing crashed at all (+11.1pp net,
but 3 true positives quietly traded for 5 false positives fixed).

So the honest order: determinism leaks corrupt behavior first, with zero
preconditions. Observability decides whether that corruption — or the
state-tiering wipe, or the checkpoint corruption — is ever noticed, rather
than silently absorbed into an aggregate score that still looks
reasonable. Skipping the determinism boundary corrupts a decision on the
first run; skipping tiering or atomicity plants a failure for the next
crash; skipping observability guarantees nobody can tell why when it does.
