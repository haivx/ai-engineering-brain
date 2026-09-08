#!/usr/bin/env python3
"""
Bonus proof: record/replay. Capture the boundary's output to a fixture file
once, then replay the WHOLE pipeline from that fixture -- making even the
"non-deterministic" half of the log reproducible, because the boundary
function used by run_pipeline() is just a parameter (see boundary.py).

Usage:
    python3 record_replay.py record    # calls the live-random stub ONCE,
                                        # writes fixtures/boundary_output.json
    python3 record_replay.py replay    # runs run_pipeline() twice using the
                                        # fixture in place of a live boundary
                                        # call -- proves the entire pipeline,
                                        # nd section included, is now
                                        # byte-identical across runs.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boundary import run_pipeline, canonical_json, non_deterministic_call, assemble_input  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_PATH = os.path.join(BASE_DIR, "fixtures", "boundary_output.json")

USER_REQUEST = {"requester": "alice", "reason": "urgent prod incident", "resource": "db-prod-01"}


def record():
    prompt = assemble_input(USER_REQUEST)
    boundary_out = non_deterministic_call(prompt)  # the ONE live/random call
    os.makedirs(os.path.dirname(FIXTURE_PATH), exist_ok=True)
    with open(FIXTURE_PATH, "w") as f:
        f.write(canonical_json(boundary_out))
    print("Recorded boundary output to {}:".format(os.path.relpath(FIXTURE_PATH, BASE_DIR)))
    print(canonical_json(boundary_out))


def replay():
    if not os.path.exists(FIXTURE_PATH):
        print("No fixture found -- run `python3 record_replay.py record` first.", file=sys.stderr)
        sys.exit(1)
    with open(FIXTURE_PATH) as f:
        fixture = json.load(f)

    def fixture_boundary_fn(_prompt):
        # ignores the live prompt entirely; always returns the recorded output
        return fixture

    _, log1 = run_pipeline(USER_REQUEST, boundary_fn=fixture_boundary_fn)
    _, log2 = run_pipeline(USER_REQUEST, boundary_fn=fixture_boundary_fn)

    full1 = canonical_json(log1)
    full2 = canonical_json(log2)

    print("=== Replayed run 1 (full log: deterministic + nd) ===")
    print(full1)
    print("\n=== Replayed run 2 (full log: deterministic + nd) ===")
    print(full2)
    print("\nfull pipeline byte-identical across replayed runs: {}".format(full1 == full2))


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("record", "replay"):
        print(__doc__)
        sys.exit(1)
    {"record": record, "replay": replay}[sys.argv[1]]()


if __name__ == "__main__":
    main()
