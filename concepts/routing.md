# Routing

The core skill of AI Engineering: **use a cheap model for the easy parts, and escalate to an expensive model only for the hard parts.**

## Why
"Which model is best" is the wrong question. The right one: "WHICH part of the work needs a strong model, and which part is fine with a cheap one?"
A task usually consists of steps of varying difficulty. Making Opus do the trivial steps too = burning money for nothing.
Making a cheap model do the hard step = broken work and wasted effort fixing it.

## The three model tiers (a frame for classifying tasks)
- **Closed frontier** (Opus, the big GPTs, Gemini Pro): for the hardest ~20% of tasks — complex architecture,
  nasty debugging, long agent loops.
- **Cheap-but-good** (Sonnet, DeepSeek Flash...): the daily driver, most everyday work.
- **Cheap open-weight / self-hosted**: odds and ends, boilerplate, extraction, formatting.
  (Model names are only examples — they rotate constantly. See references/leaderboards.md to look up the current ones.)

## Prerequisite
To route correctly you must know "which stage a cheap model is good enough for" → you must MEASURE → you need an eval set.
See concepts/eval.md. Without an eval, routing is just guesswork.

## Pitfall: compounding error
In a multi-step agent loop, a cheap model that's 5% off at each step → is completely off after 10 steps.
This is why multi-step reasoning usually has to use a strong model, even when each individual step looks simple.
