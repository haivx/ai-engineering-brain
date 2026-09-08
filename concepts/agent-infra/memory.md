# Memory (Cross-Run Tiering)

`state.md` is scoped to one run; this file is one level up — a session
(several invocations sharing state) — with a durable tier beneath that
spans every session that ever existed. Working state dies at the end of a
run; session state survives across runs but still has a bounded lifetime.

## Same pattern, one level up

An ephemeral session file is overwritten across runs; a durable
append-only log accumulates every session's activity forever. Both are
plain files — the difference is policy, not mechanism: session state is
deleted outright once it expires, the log is never deleted, only appended
to.

## Promotion order is the load-bearing part

When a session expires, its facts must be appended to the durable log —
and that write confirmed — *before* the session file is deleted. Reverse
the order, or fail to sequence it, and a crash between the two operations
reproduces `state.md`'s crash-and-wipe loss one layer up. Expiry alone
isn't what makes this safe; promotion-before-deletion is.

## A deliberate limit: expiry means "start over," not "continue"

Once a session expires, the next run starts a brand-new session with no
facts carried forward, even though the predecessor's summary is sitting in
the durable log. Continuity would require deliberately reading that
summary back on bootstrap; this proof did not build it.

## What this doesn't prove

Concurrent runs racing on the same session file, and reading facts back out
of a past summary to seed a new session, are both untested.

```mermaid
flowchart LR
    subgraph R1["Run #1 (process invocation)"]
        A1["session.json absent<br/>-> create session S1"]
    end
    subgraph R2["Run #2 (process invocation)"]
        A2["session.json = S1<br/>run_count 1 -> 2<br/>hits SESSION_MAX_RUNS"]
        A2 --> P["promote S1 facts<br/>as session_summary"]
        P --> D["delete session.json<br/>(S1 state gone from session tier)"]
    end
    subgraph R3["Run #3 (process invocation)"]
        A3["session.json absent<br/>-> create session S2"]
    end

    R1 --> R2 --> R3

    A1 -- append run event --> LOG
    A2 -- append run event --> LOG
    P -- append summary --> LOG
    A3 -- append run event --> LOG

    LOG["log.jsonl<br/>durable, append-only<br/>spans S1 AND S2, all 3 runs<br/>never dies"]

    style A1 fill:#bfdbfe,stroke:#1e3a8a
    style A2 fill:#bfdbfe,stroke:#1e3a8a
    style A3 fill:#bfdbfe,stroke:#1e3a8a
    style D fill:#fecaca,stroke:#991b1b
    style LOG fill:#bbf7d0,stroke:#166534
```

Evidence: `experiments/agent-infra/memory/` (`RUN.md`, `NOTES.md`, `diagram.mmd` / `diagram.png`).
