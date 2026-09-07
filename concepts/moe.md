# MoE & why cheap open models are cheap

## MoE (Mixture-of-Experts)
The model has N parameters in total, but each forward pass *activates* only a small fraction of them.
For example the "117B total, ~5B active/token" shape: it runs as light as a ~5B model while holding the knowledge of a large one.
→ inference is far cheaper and faster than a dense model of the same size.

## Why calling an open-weight model's API is so cheap
1. **Open-weight** = no licensing fees, you only pay for infrastructure (power/GPU).
2. **MoE** = few active parameters → less compute per token.
3. Many providers compete to host the same model → prices get pushed down.

The result: many open models are good enough for everyday work at a few percent of the price of a closed model.
