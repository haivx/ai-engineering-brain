# Working State (Single Run)

"Working state" is what a single run needs to get from its first step to
its last: scratch values, in-progress buffers, whatever a step is computing
right now. It dies when the run ends — a crash, a container recycle, or a
delete of that file should destroy nothing that already mattered.

## Two tiers, never merged

Keep ephemeral scratch (overwritten every step) strictly separate from a
durable, append-only log (one line per completed step, never rewritten).
The separation costs one extra write per step, but it's what lets the
ephemeral tier be wiped outright after a crash and the run's true progress
reconstructed from the log alone, with zero loss.

## The single-blob anti-pattern is the realistic failure

Merging scratch and history into one overwritten file looks *better* than
the two-tier design while the run is healthy — the history is right there.
The failure is invisible until a crash is followed by a wipe of that file:
every completed step's result disappears along with the scratch, because no
separate durable store ever existed. Tier separation isn't a feature; it's
insurance against a failure with no symptoms until it's too late to matter.

## What this doesn't prove

This shows the data needed to resume survives a wipe of working state — not
that a process automatically resumes execution from the recovered point.
See `concepts/agent-infra/recovery.md`.

```mermaid
flowchart TB
    subgraph RUN["One run (run_id)"]
        direction TB
        S1[Step 1] --> S2[Step 2] --> S3[Step 3] --> S4[Step 4] --> S5[Step 5]
    end

    S1 -. overwrite .-> W["working.json<br/>ephemeral, scratch only<br/>dies at end of run"]
    S2 -. overwrite .-> W
    S3 -. overwrite .-> W
    S4 -. overwrite .-> W
    S5 -. overwrite .-> W

    S1 -- append --> L["log.jsonl<br/>durable, append-only<br/>never dies"]
    S2 -- append --> L
    S3 -- append --> L
    S4 -- append --> L
    S5 -- append --> L

    W --> CRASH{{"crash after step 3<br/>+ wipe working.json"}}
    CRASH -->|working.json gone| RECON["reconstruct from log.jsonl:<br/>steps 1-3 recovered, nothing lost"]
    L --> RECON

    CRASH -.contrast.-> BLOB["ANTI-PATTERN: blob.json<br/>(scratch + history merged, one file)"]
    BLOB --> WIPE2{{"same crash + wipe"}}
    WIPE2 --> LOST["all 3 completed step results LOST<br/>(no separate durable store existed)"]

    style W fill:#fde68a,stroke:#92400e
    style L fill:#bbf7d0,stroke:#166534
    style BLOB fill:#fecaca,stroke:#991b1b
    style LOST fill:#fecaca,stroke:#991b1b
    style RECON fill:#bbf7d0,stroke:#166534
```

Evidence: `experiments/agent-infra/state/` (`RUN.md`, `NOTES.md`, `diagram.mmd` / `diagram.png`).
