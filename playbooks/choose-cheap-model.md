# Playbook: picking a cheap model as a stopgap

For when you run out of quota/tokens and need a quick replacement model.

## Steps
1. Open **llm-stats.com**, filter by the axis you need (coding / cheapest / open-weight).
2. Cross-check the REAL price on **openrouter.ai** (prices change constantly — always re-check here).
3. Classify the task at hand (see concepts/model-tiers.md):
   - Odds and ends / boilerplate / extraction → pick the cheapest open model that's still "capable".
   - Coding that needs quality → a decent open coding model with a long enough context.
   - Genuinely hard work → consider NOT downgrading (wait / top up instead).
4. In LiteLLM: change only the `MODEL` string. Change nothing else.
5. If the work matters → run it through the eval set (playbooks/build-eval-set.md) before trusting it.

## Notes
- Don't treat public tables as gospel — they're only a prior. Your eval is what decides.
- Check OpenRouter's Activity tab to confirm the request ran on the provider/price you expected.
