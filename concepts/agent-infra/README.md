# Agent Infra
This cluster maps the infrastructure concerns that show up when you move from a single prompt to a running agent: how it tracks where it is, what it remembers, what it sees at each step, how it acts on the world, how work is organized, how it recovers from failure, how you observe it, and how you keep it safe. Each file below is a short opening framing only—deep dives land in follow-up issues, one per topic.

- [state.md](./state.md) — where the agent is within a task
- [memory.md](./memory.md) — short-term vs long-term memory
- [context-engineering.md](./context-engineering.md) — what goes into context each step
- [tool-calling.md](./tool-calling.md) — the model ↔ world interface
- [orchestration.md](./orchestration.md) — single loop vs multi-agent, sub-agents
- [recovery.md](./recovery.md) — retry / fallback / loop-guard when a step fails
- [observability.md](./observability.md) — trace every step to debug
- [guardrails.md](./guardrails.md) — validate before acting
