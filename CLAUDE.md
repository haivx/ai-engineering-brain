# CLAUDE.md

Guidance for any agent (Claude Code or otherwise) working in this repo.

## What this repo is

A second-brain / knowledge base for AI Engineering. It is a git repo and an Obsidian vault at the same time. It also doubles as a context layer: point an agent at this repo and it can read `concepts/<file>.md` to follow a specific mental model.

## Golden rule

Store **ways of thinking** and **ways of looking things up** — never volatile numbers (token prices, current best model, leaderboard rankings). Those decay in weeks and do not belong in `concepts/` or `playbooks/`. For anything volatile, store only the lookup procedure + a link, in `references/`.

## Structure

- `concepts/` — durable mental models. Short framing paragraphs (3–5 sentences), not code, not proof.
- `playbooks/` — working procedures: "when you need X, follow these steps."
- `references/` — links to external sources + notes on how to look things up. No copied figures.
- `experiments/` — hands-on proof you ran yourself. Code, logs, screenshots. The most valuable folder: nobody else has this, you can't Google it.

## Working method — proof before prose

`concepts/*.md` describes a model. It must not be written from theory alone. The required order is:

1. Build a small working script/module that exercises the concept.
2. Run it and capture the evidence (log output, before/after comparison, a forced-failure-then-resume trace, etc.) under `experiments/<topic>/`.
3. If the concept benefits from a diagram, add a Mermaid diagram, render it, and verify it with Playwright (headless render → screenshot → visual check that it's correct, not broken syntax). Store the diagram source + verified screenshot in `experiments/<topic>/` alongside the run evidence.
4. Only then write or update the short framing paragraph in `concepts/<file>.md`, distilled from what step 1–3 actually showed — not from what you expected to show.

A `concepts/*.md` file that makes a claim ("the system should X") without a matching folder in `experiments/` backing it up is incomplete. When asked to "write the concept," check for the experiment first; if it doesn't exist, build it before writing the paragraph.

Never invent a new top-level folder (e.g. "practice/") for this — `experiments/` already is that folder.

## Current focus: `concepts/agent-infra/`

These files are opening-framing stubs only (see `concepts/agent-infra/README.md`); deep dives are pending. Active practice plan covers 4 topics, mapped to specific target files:

| Practice topic | Concept file | Experiment folder | Notes |
|---|---|---|---|
| State (single-run working state) | `concepts/agent-infra/state.md` | `experiments/agent-infra/state/` | Scope: what dies at the end of one run. |
| Memory (cross-run tiering) | `concepts/agent-infra/memory.md` | `experiments/agent-infra/memory/` | Scope: short-term vs long-term, session state vs durable log. Do not conflate with `state.md`. |
| Determinism at the non-deterministic boundary | `concepts/agent-infra/determinism.md` **(does not exist yet — create it)** | `experiments/agent-infra/determinism/` | Gap: no existing file in `agent-infra/` covers this. Closest neighbors are `guardrails.md` and `recovery.md`, but neither owns it. |
| Observability + eval-as-infra | `concepts/agent-infra/observability.md` | `experiments/agent-infra/observability/` | The eval-harness half of this practice feeds the existing `playbooks/build-eval-set.md`, not a new concept file. Root-level `concepts/eval.md` already owns general eval methodology — don't duplicate it here. |
| Resumability / checkpointing | `concepts/agent-infra/recovery.md` | `experiments/agent-infra/recovery/` | `recovery.md` currently frames retry/fallback/loop-guard in real time; extend it to explicitly cover checkpoint-and-resume across a restart, not just in-run retries. |

## Rules for suggestions in this repo

- When writing to `concepts/*.md`: match the existing tone — one short paragraph, no code blocks, no volatile figures, one Mermaid diagram if it aids the model.
- When asked to "build" or "prove" something: put code, logs, and screenshots in `experiments/<topic>/`, never in `concepts/`.
- Every `concepts/agent-infra/*.md` file that gets a deep-dive update should link back to its `experiments/agent-infra/<topic>/` folder as the evidence.
- Don't skip the proof step, even for a small change — a `concepts/` edit with no experiment behind it should be flagged, not written.
- Don't create new top-level folders; `concepts/`, `playbooks/`, `references/`, `experiments/` cover every case so far.
