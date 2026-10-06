# NOTES.md — what the runs actually showed

## Durability

- **Durability is knowing which side effects already happened, not saving
  messages.** The brittle loop's failure (§1) was not "lost chat history"; it
  was that a retry had no record that item-1's email was sent, so it sent it
  again. The durable version fixes this by making every side effect a
  checkpointed step: a completed step is never re-executed (§2).
- **Replay is by position, not by input.** DBOS identifies a step by
  workflow id + its ordinal in the execution; the step name is a label and a
  sanity check. On recovery the cached output is returned without calling the
  function, so the arguments passed to it (e.g. the assembled context) are
  irrelevant for already-completed steps. This is why the workflow body must
  be deterministic: branch differently on replay and cached outputs land on
  the wrong steps.
- **In-memory variables are derived, not stored.** `turns`, `summary` and
  `currentAgent` are never persisted. They are recomputed on replay because
  every value pushed into them comes from a step's cached output (§2 replay
  toy). The same holds for the compaction decision: `estimateTokens` is a
  pure function of `turns`.
- **Completed steps are exactly-once; the in-flight step is at-least-once.**
  A `sendReply` that has sent but not yet checkpointed will run again after a
  crash. The harness alone does not close this; an idempotency key
  (`workflowId:toolCallId`, stable across replay because the id comes from a
  cached model step) on the side-effecting call does. Not built here.
- **Two logs, two jobs.** The Postgres `event_log` is a projection for the
  UI/observability; DBOS's own tables are what replay reads. Truncating the
  event log does not affect recovery.

## Tool execution and the sandbox

- **The harness must own tool execution.** Letting the SDK run tools inside
  the model call (`execute`) makes the tool part of the model step, so it
  cannot be checkpointed, gated or intercepted on its own. Taking execution
  back also means the harness must append the `tool-result` itself; a
  `tool-call` without its result is a 400 from the provider on the next turn.
- **Whatever shares one step must be safe to re-run.** `runCode` and whole
  supervisor investigators run as single steps; that is only safe because
  their API is read-only. Put `sendReply` inside the sandbox and a crash
  mid-program re-sends everything before the crash point.
- **`node:vm` is not a boundary** (§3): one host function in the context
  gives back the host `process`, and one awaiting loop hangs the whole server.
  The harness's real job is to be the single choke point (`runTool` →
  `runInSandbox`); the strength of what sits behind it (isolate, worker you
  can terminate, microVM) is a deployment decision that does not change the
  architecture.

## Context

- **Compact by token budget, not turn count.** One turn can hold several tool
  calls or a large `runCode` result; turn count says nothing about size.
- **Cut whole turns only**, or a `tool-result` survives without its
  `tool-call`.
- **A memory bug becomes a side-effect bug.** If the summary drops "item-1
  was SENT", the model may decide to send again with a *new* tool call id —
  a new step DBOS has never seen. The summary eval (§4) passed 7/7 with a
  prompt that still invented "Ticket created". An eval only catches what you
  thought to check.
- **Write the summarizer prompt for its actual reader** (the same agent next
  turn): status as an enum, only actions that appear as tool calls, terse.
  Two lines replaced thirty.
- **Summary in a `system` message is a privilege escalation path**: it is
  LLM-written from customer text, then elevated to system-prompt authority.
  The AI SDK warns about this; noted, not fixed.

## Orchestration

- **Handoff transfers control; a supervisor keeps it.** A handoff is only the
  harness intercepting a fake `handoff` tool and swapping `currentAgent`; the
  conversation continues. The supervisor calls sub-agents like functions with
  `Promise.allSettled`, so a failed investigator becomes data, not a crash.
- **Least privilege enforced only by "the model doesn't see the schema" is
  hiding a button in the UI.** The executor must check. And it must check
  against the agent that *produced* the turn (`actingAgent`), not the one
  current at execution time (§5): otherwise `[handoff, issueRefund]` in one
  turn executes triage's decision with billing's privileges. The course's
  reference solution has no executor-side check at all.
- **A typed contract in two places silently drifted.** The plan schema
  allowed three investigators; the registry implemented one;
  `Record<string, Investigator>` hid it from the compiler. One union type used
  by both would have caught it.
- **Synthesis turns a recommendation into a promise.** A read-only
  supervisor told the customer "We'll refund" (§6). Prompt controls what is
  said; only the harness controls what is done. Pass known facts (which
  investigators failed) explicitly instead of letting the model infer them.

## Human-in-the-loop

- **The wait must be workflow state, not an awaited function.** `DBOS.recv`
  suspends with the pending state in Postgres; a `SIGKILL` while waiting is
  recovered by replaying to the same `recv` and waiting again (§7).
- **The gate lives in the runtime's tool loop**: not in the prompt (a
  request, not a control), not in `runTool` (it runs inside a step, and
  waiting has to happen between steps). Order in the loop: permission check →
  handoff → needs-approval → ordinary tool.
- **Fail safe**: timeout → `null` → treated as rejected. Silence is never
  consent for an irreversible action.
- **The approver needs the arguments.** An early version sent `args: "no more
  info"`; approving blind defeats the gate.
- **Approval is not bound to the action** — the hole this design and the
  course's share (§7 queue proof). Messages queue until received, the topic
  is per workflow and the payload carries no tool call id, so a double-click
  on approval #1 pre-approves approval #2. Fix: topic or payload keyed by
  `toolCallId`; the server resolves the oldest unresolved request and drops
  anything else. Also open: `/api/approve` has no authentication.

## Observability side-notes

- A workflow that throws without emitting `workflow.failed` stays "running"
  forever in any consumer that counts started vs finished (the inspector
  showed "Thinking…" for a long-dead run). Terminal events need a `finally`.
- Emitting the full accumulated text on every delta looked fine in the UI
  but wrote N copies of the answer to Postgres (186 vs 126 events).
- A per-item `count(*)` over the event log is already an eval: it checks what
  the system *did*, not what the model *said*.

## What this does not prove

Real-model behaviour is from a handful of live runs, not a dataset. No
idempotency keys, no isolate-based sandbox, no auth, no concurrent
workflows, no fix for the approval-binding hole yet. The scripted runs use a
fake model and prove harness properties only.
