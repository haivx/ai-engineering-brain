#!/usr/bin/env python3
"""
Compare two eval result files produced by eval_harness.py and print a
before/after table. This is the "did the change help?" step: it answers the
question from the numbers in results/*.json alone, no re-reading of logs
required (though the logs are what you'd open next to find out *why*).

Usage:
    python3 compare_runs.py --before baseline --after stricter
"""

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results")


def load(tag):
    path = os.path.join(RESULTS_DIR, "eval_{}.json".format(tag))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Compare two eval_harness.py result files.")
    parser.add_argument("--before", required=True, help="tag of the baseline run")
    parser.add_argument("--after", required=True, help="tag of the changed run")
    args = parser.parse_args()

    before = load(args.before)
    after = load(args.after)
    b_sum, a_sum = before["summary"], after["summary"]

    print("Comparing: {} (threshold={}) -> {} (threshold={})".format(
        args.before, b_sum["threshold"], args.after, a_sum["threshold"]))
    print()
    print("{:<16} {:>10} {:>10} {:>10}".format("metric", "before", "after", "delta"))
    for key in ("passed", "failed", "errored"):
        delta = a_sum[key] - b_sum[key]
        print("{:<16} {:>10} {:>10} {:>+10}".format(key, b_sum[key], a_sum[key], delta))
    delta_rate = a_sum["pass_rate"] - b_sum["pass_rate"]
    print("{:<16} {:>9.1%} {:>9.1%} {:>+9.1%}".format("pass_rate", b_sum["pass_rate"], a_sum["pass_rate"], delta_rate))
    print()

    verdict = "IMPROVED" if delta_rate > 0 else ("REGRESSED" if delta_rate < 0 else "NO CHANGE")
    print("Verdict: {} ({:+.1%} pass rate)".format(verdict, delta_rate))
    print()

    # Per-case diff: which specific cases flipped, in which direction.
    before_by_id = {c["case_id"]: c for c in before["cases"]}
    after_by_id = {c["case_id"]: c for c in after["cases"]}
    flips = []
    for case_id, b_case in before_by_id.items():
        a_case = after_by_id.get(case_id)
        if a_case is None:
            continue
        if b_case["passed"] != a_case["passed"]:
            direction = "FAIL -> PASS" if a_case["passed"] else "PASS -> FAIL"
            flips.append((case_id, direction, b_case["predicted"], a_case["predicted"], b_case["expected"]))

    if flips:
        print("Per-case flips ({} of {} cases changed outcome):".format(len(flips), len(before_by_id)))
        print("{:<28} {:<14} {:<12} {:<12} {}".format("case_id", "direction", "before_pred", "after_pred", "expected"))
        for case_id, direction, b_pred, a_pred, expected in flips:
            print("{:<28} {:<14} {:<12} {:<12} {}".format(case_id, direction, str(b_pred), str(a_pred), str(expected)))
    else:
        print("No case changed outcome between the two runs.")


if __name__ == "__main__":
    main()
