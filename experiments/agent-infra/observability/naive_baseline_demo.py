#!/usr/bin/env python3
"""
Contrast piece, NOT the real harness: what a "just print stuff" version of
this eval would look like, to make the argument for structured logging
concrete rather than asserted.

This naive version runs the exact same cases through the exact same router,
but only ever prints a running pass count and catches errors with one bare
`except Exception: print("case failed")`. Run it side by side with
eval_harness.py to see the difference in what each lets you answer about
the SAME failure.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "eval_cases.json"), "r", encoding="utf-8") as f:
    cases = json.load(f)

passed = 0
for case in cases:
    try:
        normalized = router.normalize(case["input"])
        tokens = router.tokenize(normalized)
        scores = router.score(tokens)
        predicted, _ = router.decide(scores, threshold=0.0)
        if predicted == case["expected"]:
            passed += 1
        else:
            print("case failed")
    except Exception:
        print("case failed")

print("{}/{} passed".format(passed, len(cases)))
