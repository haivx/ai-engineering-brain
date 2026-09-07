# The three model tiers (detailed version)

See also concepts/routing.md — this is the classification table for deciding when to escalate.

| Tier | Use for | Characteristics |
|---|---|---|
| Closed frontier | The hardest ~20%: complex architecture, nasty debugging, long agent loops | Expensive, strongest, hard to replace |
| Cheap-but-good | Daily driver: most everyday coding | Balanced price/quality |
| Cheap open / self-hosted | Boilerplate, extraction, classification, formatting, tests | Dirt cheap, good enough for easy work |

## Decision rules
1. Which tier does this task belong to? (by real difficulty, not by feel)
2. Has the cheapest model in that tier been MEASURED as good enough? (eval set)
3. If unsure → try the cheaper tier first; escalate if the eval catches errors.

## When you're "out of tokens and need a stopgap"
- Odds and ends → the cheap open tier.
- Coding that needs quality → the cheap-but-good tier.
- Genuinely hard work → DON'T downgrade. Waiting / topping up beats letting a cheap model break it and then fixing it.

(Specific model names rotate constantly — look up the current ones in references/leaderboards.md.)
