# Context Engineering: History, State, Context

Context engineering decides what goes into the model's window at each step.
The useful split is three things that are easy to conflate: **history** (the
full, append-only record of what happened, which lives in storage), **state**
(the small set of facts the agent must not lose: what was already done, to
whom, for how much), and **context** (what is assembled and sent this one
step). Context is rebuilt every step from the other two; it is never the
place where anything is kept.

## Assemble in a fixed order, compact by size

Each step: system instructions, then the pinned task, then a summary of
older turns if one exists, then the most recent turns verbatim. Compaction
triggers on an estimated token budget, not a turn count, because one turn
can carry several tool calls or one very large tool result. Use two
thresholds (compact above a high mark, keep below a lower one) so it does
not fire on every step. Cut only whole turns, or a tool result survives
without the call that produced it. Run this way, the context size per step
oscillated within a band instead of growing with the conversation.

## A memory bug becomes a side-effect bug

The summary is not a convenience; it is where state survives compaction. If
it drops "this item was already sent", the model can decide to send again
with a *new* call id, which no durability layer has seen before, so nothing
stops it. An eval of the summary passed every check while the summary still
invented an action ("ticket created") that never happened. An eval only
catches what it was written to check.

## Write the summarizer prompt for its real reader

The reader is the same agent on its next turn, not a human. Rewriting the
prompt that way (status as a small closed set, record only actions that
appear as tool calls, terse) turned a long markdown report with an invented
action into two exact lines, and the same eval still passed. After a long
compacted run, counting side effects per item in the event log showed each
one exactly once.

## Where you put the summary is a permission decision

A summary written by a model from customer text and then placed in a
system-role message gains system-prompt authority. That is a prompt-injection
path, observed and noted but not fixed here.

## What this doesn't prove

The live compaction run was a handful of real-model runs, not a dataset.
Token counts were estimated, not taken from a tokenizer. Retrieval and
long-term memory across sessions are out of scope (see `memory.md`).

Evidence: `experiments/agent-infra/harness/` (`RUN.md` §4, `NOTES.md` "Context", `logs/04_memory_contract.log`).
