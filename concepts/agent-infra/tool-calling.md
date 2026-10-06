# Tool Calling: the Harness Owns Execution

Tool calling is the interface through which a model acts on and observes
the world. The model only *proposes* a call; whatever turns that proposal
into an effect is infrastructure, and it has to belong to the harness, not
to the model SDK.

## Take execution back from the SDK

If a tool runs inside the model call (the SDK's built-in auto-execute), it
becomes part of the model step: it cannot be checkpointed, gated, permission-
checked or intercepted on its own. Taking execution back puts every call
through one choke point the harness controls. It also hands the harness a
bookkeeping duty: every tool call must be answered with its tool result in
the next turn's messages, including denials and rejections, or the provider
refuses the conversation.

## Everything inside one step must be safe to re-run

A step is the unit of replay. Code Mode (the model writes one small program
against a typed API instead of chaining many calls) is a real win for
multi-step lookups, because the whole program becomes one step. That is only
safe because the API inside it is read-only. Put a side-effecting call inside
the same program and a crash mid-program re-fires everything before the crash
point. Side effects get their own step each.

## The choke point is the architecture; the sandbox is a deployment choice

An in-process VM is not a security boundary. In the experiment, one host
function passed into the sandbox was enough to climb out and reach the host
process, and one awaiting infinite loop slipped past the synchronous timeout
and hung the entire server. What the harness must guarantee is that every
call goes through a single function. How strong the isolation behind that
function is (an isolate, a killable worker, a microVM) can change without
touching the rest of the design.

## What this doesn't prove

No real isolation backend was built or tested; the escape and hang were
demonstrated, not fixed. Tool-schema quality and how well a model picks tools
were not measured.

Evidence: `experiments/agent-infra/harness/` (`RUN.md` §3, `NOTES.md` "Tool execution and the sandbox", `logs/03_sandbox_checks.log`).
