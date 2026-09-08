#!/usr/bin/env python3
"""
Proof 1: the disciplined boundary. Same input, run twice.

Demonstrates:
  - the 'nd' half of the log (the boundary's raw output) DIFFERS between
    the two runs -- expected, that's the non-determinism we isolated.
  - the 'deterministic' half of the log is BYTE-IDENTICAL between the two
    runs -- everything outside the boundary (input assembly, parsing,
    decision) behaved as pure code should.

Usage:
    python3 run_stable.py            # stub boundary (offline, default)
    python3 run_stable.py --live     # real LLM call via OPENROUTER_API_KEY,
                                      # falls back to the stub with a warning
                                      # if the key is missing or the call fails
"""
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boundary import run_pipeline, canonical_json, non_deterministic_call, live_llm_call  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")


def make_boundary_fn(live):
    if not live:
        return non_deterministic_call

    def _fn(prompt):
        try:
            return live_llm_call(prompt)
        except Exception as exc:  # noqa: BLE001 - deliberate: any failure -> stub
            print("WARNING: live LLM call failed ({}); falling back to stub".format(
                type(exc).__name__), file=sys.stderr)
            return non_deterministic_call(prompt)
    return _fn


def diff_block(label_a, text_a, label_b, text_b):
    lines = list(difflib.unified_diff(
        text_a.splitlines(keepends=True),
        text_b.splitlines(keepends=True),
        fromfile=label_a, tofile=label_b,
    ))
    return "".join(lines) if lines else "(no diff -- byte-identical)"


def main():
    live = "--live" in sys.argv
    boundary_fn = make_boundary_fn(live)

    user_request = {"requester": "alice", "reason": "urgent prod incident", "resource": "db-prod-01"}

    decision1, log1 = run_pipeline(user_request, boundary_fn=boundary_fn)
    decision2, log2 = run_pipeline(user_request, boundary_fn=boundary_fn)

    det1 = canonical_json(log1["deterministic"])
    det2 = canonical_json(log2["deterministic"])
    nd1 = canonical_json(log1["nd"])
    nd2 = canonical_json(log2["nd"])

    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "stable_run1.json"), "w") as f:
        f.write(canonical_json(log1))
    with open(os.path.join(LOG_DIR, "stable_run2.json"), "w") as f:
        f.write(canonical_json(log2))

    print("=== Run 1: deterministic log ===")
    print(det1)
    print("\n=== Run 2: deterministic log ===")
    print(det2)

    print("\n=== Run 1: non-deterministic (boundary) log ===")
    print(nd1)
    print("\n=== Run 2: non-deterministic (boundary) log ===")
    print(nd2)

    print("\n=== Diff: deterministic logs (run1 vs run2) ===")
    print(diff_block("run1.deterministic", det1 + "\n", "run2.deterministic", det2 + "\n"))

    print("\n=== Diff: non-deterministic logs (run1 vs run2) ===")
    print(diff_block("run1.nd", nd1 + "\n", "run2.nd", nd2 + "\n"))

    det_identical = det1 == det2
    nd_identical = nd1 == nd2
    print("\n=== Summary ===")
    print("deterministic logs byte-identical: {}".format(det_identical))
    print("non-deterministic logs byte-identical: {}".format(nd_identical))
    print("final decision run1: {}".format(decision1))
    print("final decision run2: {}".format(decision2))

    if not det_identical:
        print("FAIL: deterministic scaffolding leaked non-determinism.", file=sys.stderr)
        sys.exit(1)
    if nd_identical:
        print("NOTE: nd logs happened to match this time (possible with a small "
              "template pool) -- re-run to see them diverge; this does not "
              "invalidate the deterministic-side proof above.")


if __name__ == "__main__":
    main()
