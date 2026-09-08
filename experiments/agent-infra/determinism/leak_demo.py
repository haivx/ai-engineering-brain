#!/usr/bin/env python3
"""
Proof 2 (the failure mode): what happens when non-determinism LEAKS past the
boundary into code that is supposed to be deterministic. Same input, run
twice, through a pipeline built the way real code often accidentally is.

Three separate leaks, each demonstrated in isolation and then combined:

  1. naive_parse_output() -- parses the boundary's text by looking at its
     FIRST WORD instead of scanning for a stable keyword. The label it
     recovers now depends on which phrasing template the boundary happened
     to pick, not on the underlying (deterministic) verdict.

  2. decide_with_timestamp() -- stamps time.time() into the "decision"
     record. Wall-clock time is non-determinism that has nothing to do
     with the boundary at all, injected directly into scaffolding code.

  3. summarize_tags_leaky() -- builds a summary string by iterating a
     `set()` of tags. Set/dict-of-arbitrary-objects iteration order is not
     guaranteed stable across runs in general (and str-hash randomization
     specifically varies dict/set ordering for str keys across separate
     `python3` process invocations unless PYTHONHASHSEED is fixed) -- a
     classic "hidden randomness" bug that has nothing to do with an LLM.

Each leak is shown diverging between two runs of the identical input, then
the disciplined pipeline (boundary.run_pipeline) is run on the same input
for direct contrast: same divergence pressure (a real non-deterministic
boundary call), stable deterministic log.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boundary import assemble_input, non_deterministic_call, canonical_json, run_pipeline  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")


# ---- Leak 1: naive parsing keyed off incidental output formatting --------

def naive_parse_output(boundary_output):
    """BAD: keys off the first word of the raw text instead of scanning for
    a stable marker. Different templates for the SAME verdict start with
    different words, so this misclassifies depending on which template the
    boundary happened to pick.
    """
    first_word = boundary_output["raw_text"].split()[0].strip(",.").lower()
    # only a couple of templates literally start with "approve"/"reject"
    if first_word == "approve":
        return {"label": "APPROVE"}
    if first_word == "reject":
        return {"label": "REJECT"}
    return {"label": "UNKNOWN"}  # "Yes,", "This", "No," all fall through here


# ---- Leak 2: wall-clock timestamp stamped into "deterministic" state -----

def decide_with_timestamp(parsed):
    """BAD: decision logic that stamps time.time() into its own record.
    The action is still derived correctly from `parsed`, but the record is
    no longer reproducible -- it now differs on every single call, even
    back-to-back calls in the same process.
    """
    action = "grant_access" if parsed["label"] == "APPROVE" else "deny_access"
    return {"action": action, "decided_at": time.time()}


# ---- Leak 3: set iteration order treated as if it were stable -----------

def summarize_tags_leaky(tags):
    """BAD: joins a set() of string tags directly. CPython randomizes str
    hashing per process by default (PYTHONHASHSEED=random), so the
    iteration order of a set of strings is not guaranteed stable across
    separate process invocations, even though within one process it looks
    perfectly deterministic (it doesn't reshuffle mid-run).
    """
    return ",".join(set(tags))


def leaky_pipeline(user_request, tags):
    prompt = assemble_input(user_request)
    boundary_out = non_deterministic_call(prompt)
    parsed = naive_parse_output(boundary_out)
    decision = decide_with_timestamp(parsed)
    summary = summarize_tags_leaky(tags)
    return {
        "deterministic_looking": {
            "assemble_input": prompt,
            "parse_output": parsed,
            "decide": decision,
            "tag_summary": summary,
        },
        "nd": {"boundary_call": boundary_out},
    }


def run_in_subprocess(snippet):
    """Run a tiny snippet in a fresh `python3` process so PYTHONHASHSEED's
    per-process randomization actually varies (it does not change within
    one already-running process, so leak 3 needs separate processes to show)."""
    result = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=BASE_DIR, capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    user_request = {"requester": "alice", "reason": "urgent prod incident", "resource": "db-prod-01"}
    tags = ["prod", "db", "urgent", "incident", "oncall"]

    print("=== Leak 1 + 2: naive parse + timestamped decide, same input, two runs ===")
    log1 = leaky_pipeline(user_request, tags)
    log2 = leaky_pipeline(user_request, tags)
    det1 = canonical_json(log1["deterministic_looking"])
    det2 = canonical_json(log2["deterministic_looking"])

    with open(os.path.join(LOG_DIR, "leaky_run1.json"), "w") as f:
        f.write(canonical_json(log1))
    with open(os.path.join(LOG_DIR, "leaky_run2.json"), "w") as f:
        f.write(canonical_json(log2))

    print("\n--- run1 'deterministic-looking' log ---")
    print(det1)
    print("\n--- run2 'deterministic-looking' log ---")
    print(det2)
    print("\nidentical: {}".format(det1 == det2))
    if det1 != det2:
        print("DIVERGED: parse_output.label and/or decide.decided_at differ "
              "between two runs of the SAME input, in code that looks "
              "deterministic at a glance.")

    print("\n=== Leak 3: set() iteration order across separate process runs ===")
    snippet = (
        "import sys; sys.path.insert(0, {!r}); "
        "from leak_demo import summarize_tags_leaky; "
        "print(summarize_tags_leaky({!r}))"
    ).format(BASE_DIR, tags)
    out_a = run_in_subprocess(snippet)
    out_b = run_in_subprocess(snippet)
    print("process A tag_summary: {}".format(out_a))
    print("process B tag_summary: {}".format(out_b))
    print("identical across processes: {}".format(out_a == out_b))

    print("\n=== Contrast: the disciplined pipeline on the SAME input/pressure ===")
    _, good_log1 = run_pipeline(user_request)
    _, good_log2 = run_pipeline(user_request)
    good_det1 = canonical_json(good_log1["deterministic"])
    good_det2 = canonical_json(good_log2["deterministic"])
    print("disciplined deterministic log run1 == run2: {}".format(good_det1 == good_det2))
    print(good_det1)


if __name__ == "__main__":
    main()
