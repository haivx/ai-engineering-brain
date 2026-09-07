# Orchestration
Orchestration is the architecture that governs how an agent's work gets done: a single loop handling everything itself, or a coordinator delegating pieces of the task to specialized sub-agents. The choice shapes how well a system scales to complex, multi-part tasks and how failures in one part are isolated from the rest. Multi-agent orchestration can parallelize work and keep individual contexts focused, but it introduces its own overhead—coordination, hand-offs, and aggregation—that a single-loop agent never has to deal with.

```mermaid
flowchart TB
    subgraph Single-loop
        direction TB
        A[Agent] -->|reasons, calls tools,<br/>writes final answer| A
    end

    subgraph Multi-agent
        direction TB
        C[Coordinator] -->|delegates subtask| S1[Sub-agent A]
        C -->|delegates subtask| S2[Sub-agent B]
        S1 -->|reports result| C
        S2 -->|reports result| C
        C -->|aggregates & responds| Out[Final answer]
    end
```
