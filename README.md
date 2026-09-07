# ai-engineering-brain

A second brain (knowledge base) for **AI Engineering**.
It is a Git repo and, at the same time, an Obsidian vault (just "Open folder as vault").

## What this KB is for
- A place to look up what you've learned, kept organized.
- **Context layer for Claude Code**: since everything is markdown inside the repo, the agent can read it.
  Example: "apply routing as described in `concepts/routing.md`" → it reads the file and follows it.

## The golden rule
> Store **ways of thinking** and **ways of looking things up** — not **numbers**.

Token prices, the currently-best model, leaderboards → they decay within weeks. Do NOT copy them here.
Mental models (routing, eval, tiers...) → they don't change. THOSE are worth writing down.
For volatile stuff: store only the *lookup procedure* + links (see `references/`).

## Structure
- `concepts/`     — DURABLE knowledge: mental models, principles.
- `playbooks/`    — working procedures: "when you need X, follow these steps".
- `references/`   — links to external sources + NOTES ON HOW TO LOOK THINGS UP (no copied figures).
- `experiments/`  — eval results you ran YOURSELF. The most valuable part: nobody else has it, you can't Google it.

## Current table of contents
- concepts: routing · eval · model-tiers · moe · inference-providers
- playbooks: choose-cheap-model · build-eval-set
- references: leaderboards
