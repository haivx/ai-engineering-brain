# Inference providers: speed vs price

## Keep two things separate
- The **model** determines the QUALITY of the answer.
- The **provider** (whoever runs the inference) determines how FAST or SLOW you get it, and at what PRICE.
The same open model can run on many providers with nearly identical quality but wildly different price & speed.

## The core trade-off
- A high-speed provider (e.g. inference-specialized chips, throughput in the thousands of tokens/s) → FAST but MORE EXPENSIVE.
- A commodity provider → much CHEAPER but slower.
Pick fast when: realtime UX, multi-step agent loops, demos that need to feel smooth.
Pick cheap when: batch work that isn't urgent, learning/experimenting.

## LiteLLM + OpenRouter (the current stack)
- **LiteLLM**: a unified wrapper — call every provider through the same OpenAI-style `completion()` function.
  Switching models = switching one string.
- **OpenRouter**: a one-API-key router giving access to many models/providers. Pay up front with credits,
  deducted silently per token (no payment-confirmation screen on every call).
- Force a specific provider: pass `{"provider": {"order": ["<name>"]}}` via `extra_body`.
  Add `"allow_fallbacks": false` if you want a hard pin with no falling back to another host.
- Note: if the specified provider is at capacity, OpenRouter falls back automatically → check the Activity tab
  to see which host the request ACTUALLY ran on (price/host are shown there).

## Cost safety
The fastest way to burn money: an agent stuck in a retry loop running thousands of times.
→ Set a spending limit on the dashboard RIGHT from the start.
