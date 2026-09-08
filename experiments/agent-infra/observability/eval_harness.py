#!/usr/bin/env python3
"""
Minimal eval harness + structured logger for router.py.

Usage:
    python3 eval_harness.py --threshold 0.0 --tag baseline
    python3 eval_harness.py --threshold 0.2 --tag stricter

For each case in eval_cases.json, runs the router pipeline
(normalize -> tokenize -> score -> decide) one step at a time, emitting one
JSONL record per step to logs/run_<tag>.jsonl. Every record carries the same
run_id (so all steps of one run correlate) and a case_id + step_seq (so all
steps of one case, in order, correlate). A run-level summary record is
appended at the end.

The eval score (pass rate) is computed purely from each case's final
predicted label vs its expected label — deterministic, no LLM judge, no
network. A step that raises is caught, logged with status="error", and the
case is scored as a fail without killing the rest of the run.

Stdlib only. Python 3.9 compatible.
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CASES_PATH = os.path.join(HERE, "eval_cases.json")
LOGS_DIR = os.path.join(HERE, "logs")
RESULTS_DIR = os.path.join(HERE, "results")

PIPELINE = [
    ("normalize", lambda ctx: router.normalize(ctx["text"])),
    ("tokenize", lambda ctx: router.tokenize(ctx["normalized"])),
    ("score", lambda ctx: router.score(ctx["tokens"])),
    # decide is handled separately below because it also takes `threshold`,
    # which is a run parameter rather than the previous step's output.
]


def _truncate(value, limit=200):
    """Keep log records small and diffable; never let one field blow up the line."""
    s = repr(value)
    return s if len(s) <= limit else s[:limit] + "...<truncated>"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class JsonlLogger:
    """Append-only structured logger. One JSON object per line, one line per event."""

    def __init__(self, path):
        self.path = path
        self._fh = open(path, "a", encoding="utf-8")

    def emit(self, **fields):
        self._fh.write(json.dumps(fields, sort_keys=True) + "\n")
        self._fh.flush()

    def close(self):
        self._fh.close()


def run_case(case, threshold, run_id, logger):
    """
    Run one eval case through the instrumented pipeline.
    Returns a dict summarizing the case outcome (used for the eval score).
    """
    case_id = case["id"]
    ctx = {"text": case["input"]}
    step_seq = 0
    failed_step = None
    error_message = None

    # Steps that don't need the run threshold.
    for step_name, step_fn in PIPELINE:
        step_seq += 1
        t0 = time.perf_counter()
        step_input = dict(ctx)
        try:
            output = step_fn(ctx)
            duration_ms = (time.perf_counter() - t0) * 1000
            logger.emit(
                run_id=run_id, case_id=case_id, step_seq=step_seq,
                step=step_name, status="ok",
                input=_truncate(step_input.get("text") if step_name == "normalize"
                                 else step_input.get("normalized") if step_name == "tokenize"
                                 else step_input.get("tokens")),
                output=_truncate(output),
                duration_ms=round(duration_ms, 4),
                error=None, timestamp=now_iso(),
            )
            key = {"normalize": "normalized", "tokenize": "tokens", "score": "scores"}[step_name]
            ctx[key] = output
        except Exception as exc:  # noqa: BLE001 - deliberately broad: any step can fail
            duration_ms = (time.perf_counter() - t0) * 1000
            failed_step = step_name
            error_message = "{}: {}".format(type(exc).__name__, exc)
            logger.emit(
                run_id=run_id, case_id=case_id, step_seq=step_seq,
                step=step_name, status="error",
                input=_truncate(step_input.get("text")),
                output=None, duration_ms=round(duration_ms, 4),
                error=error_message, timestamp=now_iso(),
            )
            break

    predicted = None
    confidence = None
    if failed_step is None:
        step_seq += 1
        t0 = time.perf_counter()
        try:
            predicted, confidence = router.decide(ctx["scores"], threshold)
            duration_ms = (time.perf_counter() - t0) * 1000
            logger.emit(
                run_id=run_id, case_id=case_id, step_seq=step_seq,
                step="decide", status="ok",
                input=_truncate({"scores": ctx["scores"], "threshold": threshold}),
                output=_truncate({"predicted": predicted, "confidence": confidence}),
                duration_ms=round(duration_ms, 4),
                error=None, timestamp=now_iso(),
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.perf_counter() - t0) * 1000
            failed_step = "decide"
            error_message = "{}: {}".format(type(exc).__name__, exc)
            logger.emit(
                run_id=run_id, case_id=case_id, step_seq=step_seq,
                step="decide", status="error",
                input=_truncate(ctx.get("scores")), output=None,
                duration_ms=round(duration_ms, 4),
                error=error_message, timestamp=now_iso(),
            )

    passed = (failed_step is None) and (predicted == case["expected"])
    outcome = {
        "case_id": case_id,
        "expected": case["expected"],
        "predicted": predicted,
        "confidence": confidence,
        "passed": passed,
        "errored": failed_step is not None,
        "failed_step": failed_step,
        "error": error_message,
    }
    logger.emit(
        run_id=run_id, case_id=case_id, step_seq=step_seq + 1,
        step="case_result", status="ok" if not outcome["errored"] else "error",
        input=_truncate(case["input"]), output=_truncate(outcome),
        duration_ms=None, error=error_message, timestamp=now_iso(),
    )
    return outcome


def main():
    parser = argparse.ArgumentParser(description="Run the router eval with structured logging.")
    parser.add_argument("--threshold", type=float, required=True,
                         help="Minimum confidence to accept the top category (else -> unknown).")
    parser.add_argument("--tag", type=str, required=True,
                         help="Short label for this run, used in log/result filenames.")
    args = parser.parse_args()

    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    with open(CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    run_id = "run-{}-{}".format(args.tag, uuid.uuid4().hex[:8])
    log_path = os.path.join(LOGS_DIR, "run_{}.jsonl".format(args.tag))
    # Fresh log per run so re-running a tag doesn't silently accumulate stale records.
    if os.path.exists(log_path):
        os.remove(log_path)
    logger = JsonlLogger(log_path)

    outcomes = []
    t_run0 = time.perf_counter()
    for case in cases:
        outcomes.append(run_case(case, args.threshold, run_id, logger))
    run_duration_ms = (time.perf_counter() - t_run0) * 1000

    passed = sum(1 for o in outcomes if o["passed"])
    errored = sum(1 for o in outcomes if o["errored"])
    total = len(outcomes)
    pass_rate = passed / total if total else 0.0

    summary = {
        "run_id": run_id,
        "tag": args.tag,
        "threshold": args.threshold,
        "total_cases": total,
        "passed": passed,
        "failed": total - passed,
        "errored": errored,
        "pass_rate": round(pass_rate, 4),
        "run_duration_ms": round(run_duration_ms, 4),
        "timestamp": now_iso(),
    }
    logger.emit(
        run_id=run_id, case_id=None, step_seq=None, step="run_summary",
        status="ok", input=_truncate({"threshold": args.threshold, "total_cases": total}),
        output=_truncate(summary), duration_ms=round(run_duration_ms, 4),
        error=None, timestamp=now_iso(),
    )
    logger.close()

    result_path = os.path.join(RESULTS_DIR, "eval_{}.json".format(args.tag))
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "cases": outcomes}, f, indent=2)

    # Human-readable console summary (in addition to, never instead of, the JSONL log).
    print("run_id:        {}".format(run_id))
    print("tag:           {}".format(args.tag))
    print("threshold:     {}".format(args.threshold))
    print("cases:         {}".format(total))
    print("passed:        {}".format(passed))
    print("failed:        {}".format(total - passed))
    print("errored:       {}".format(errored))
    print("pass_rate:     {:.1%}".format(pass_rate))
    print("log:           {}".format(os.path.relpath(log_path, HERE)))
    print("result:        {}".format(os.path.relpath(result_path, HERE)))
    print()
    print("{:<28} {:<10} {:<10} {:<6} {}".format("case_id", "expected", "predicted", "pass", "note"))
    for o in outcomes:
        note = "ERROR: {}".format(o["error"]) if o["errored"] else ""
        print("{:<28} {:<10} {:<10} {:<6} {}".format(
            o["case_id"], str(o["expected"]), str(o["predicted"]), "PASS" if o["passed"] else "FAIL", note
        ))


if __name__ == "__main__":
    main()
