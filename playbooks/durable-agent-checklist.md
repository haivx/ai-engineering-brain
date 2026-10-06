# Playbook: reviewing an agent harness before it touches real side effects

For when an agent loop is about to send, charge, refund or write anything
real. Each item is something that broke, or was shown to be missing, in
`experiments/agent-infra/harness/`.

## Durability
1. Every model turn and every side-effecting tool call is its own durable
   step. Not "save the messages": record which effects already happened.
2. The workflow body between steps is deterministic: no clock, randomness
   or external reads outside a step. In-memory state is only built from
   step outputs.
3. Side-effecting calls carry an idempotency key (workflow id + tool call
   id), because the step in flight at a crash runs again.
4. Kill the process mid-run (`SIGKILL`, not a clean shutdown), restart,
   and count side effects per target in the log. Expect exactly one each.
5. Terminal events are emitted in a `finally`, so a thrown workflow does
   not look "running" forever.

## Tools
6. The harness executes tools, not the SDK; every tool call gets a tool
   result back, including denials.
7. Anything grouped into one step (Code Mode programs, sub-agents) uses a
   read-only API only.
8. Do not trust `node:vm` or similar in-process sandboxes. Probe with a
   constructor escape and an awaiting infinite loop before believing it.

## Context
9. Compaction triggers on a token estimate, cuts whole turns only, and
   has a lower keep threshold than its trigger.
10. The summary keeps every completed side effect, and only those that
    appear as tool calls. Check it against the event log, not only with an
    eval of the text.
11. Model-written summaries are not placed with system-prompt authority.

## Control
12. Permission is checked in the executor against the agent that produced
    the turn.
13. Irreversible tools wait for durable human approval showing the full
    arguments; timeout means reject.
14. The approval names the tool call it approves, and the approve endpoint
    is authenticated.
15. A supervisor's synthesizer is told which actions were and were not
    taken, and which sub-agents failed.

## Notes
- A per-target `count(*)` over the event log is already an eval: it checks
  what the system did, not what the model said.
- Items 3, 5, 11 and 14 are open in the experiment; treat them as known gaps,
  not solved patterns.
