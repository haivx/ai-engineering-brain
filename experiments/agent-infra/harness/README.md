# experiments/agent-infra/harness/

A mini agent **harness** (runtime) rebuilt from an empty starter, module by
module, while working through Scott Moss's *Harness Engineering & Agent
Orchestration* course (Master.dev, Oct 2026; course repo
`Hendrixer/harness-engineering`). The agent is deliberately boring (support
triage). The harness is the subject: it owns the loop, durability, sandboxing,
context, routing, supervision and human approval.

Unlike the other folders under `experiments/agent-infra/`, this one is one
system exercised from seven angles, so it backs several concept files at once.

| Module | What the harness gained | Backs concept file | Evidence |
|---|---|---|---|
| 1 Agent loop | hand-driven `while` loop, event stream | (baseline for everything else) | `logs/01_brittle_crash_retry.log` |
| 2 Durable execution | every model turn / tool call is a DBOS step; Postgres event log | `recovery.md`, `determinism.md` | `logs/02_durable_crash.log`, `logs/02_replay_toy.log` |
| 3 Sandbox + Code Mode | `runCode` tool, `node:vm` sandbox, read-only API | `tool-calling.md`, `guardrails.md` | `logs/03_sandbox_checks.log` |
| 4 Memory | History / State / Context split, token-budget compaction | `context-engineering.md` | `logs/04_memory_contract.log`, RUN.md §4 |
| 5 Handoff | agents as data, least privilege, executor-side permission check | `orchestration.md`, `guardrails.md` | `logs/05_permission_escalation.log`, RUN.md §5 |
| 6 Supervisor | plan → parallel read-only investigators → fan-in → synthesize | `orchestration.md` | `logs/06_supervisor_chaos.log`, RUN.md §6 |
| 7 Human-in-the-loop | durable approval gate (`DBOS.recv` / `DBOS.send`) | `recovery.md`, `guardrails.md` | `logs/07_*.log` |

- `RUN.md` — what was run and what came out, section per module.
- `NOTES.md` — what the runs actually taught, including the holes the
  course's reference solution does not cover.
- `proofs/` — three standalone scripts small enough to read in one sitting.
- `diagram.mmd` / `diagram.png` — the harness spine with every gate on it;
  `diagram-orchestration.*` (handoff vs supervisor) and `diagram-approval.*`
  (approval wait across a `SIGKILL`). All rendered and verified with
  `../_diagram-harness/`.

The harness code itself lives in the course repo on the learner's
`my-harness` branch, not here. This folder keeps only the evidence and the
small proofs that do not depend on the course code.
