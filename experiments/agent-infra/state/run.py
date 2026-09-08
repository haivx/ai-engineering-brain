#!/usr/bin/env python3
"""
Proof for concepts/agent-infra/state.md — single-run WORKING state.

Two tiers are demonstrated, kept in separate files on purpose:
  working.json  — scratch state for the CURRENT run only. Overwritten every
                  step. Meant to die with the process. No historical value.
  log.jsonl     — append-only durable record of every step that actually
                  completed. Never overwritten, never truncated.

And, as a contrast, one ANTI-pattern:
  blob.json     — a single-blob design that merges scratch state and history
                  into one object. Shows what a "wipe" costs when there is
                  no tier separation to fall back on.

All file paths are relative to this script's own directory so it behaves
the same run from the repo root or from inside this folder.

Commands:
  python3 run.py run   --run-id R1 [--crash-at N]
  python3 run.py wipe-working
  python3 run.py reconstruct --run-id R1
  python3 run.py blob-run --run-id R2 [--crash-at N]
  python3 run.py wipe-blob
  python3 run.py reset
"""
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_PATH = os.path.join(BASE_DIR, "working.json")
LOG_PATH = os.path.join(BASE_DIR, "log.jsonl")
BLOB_PATH = os.path.join(BASE_DIR, "blob.json")

STEPS = 5


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def append_log(record):
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def read_log():
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def step_result(run_id, step):
    # Deterministic "computation" so re-runs are reproducible.
    return step * step


def cmd_run(run_id, crash_at):
    print(f"[run] starting run_id={run_id}, {STEPS} steps, tiers: working.json (ephemeral) + log.jsonl (durable)")
    for step in range(1, STEPS + 1):
        result = step_result(run_id, step)

        # Tier 1: working state — full overwrite every step. This is the
        # ONLY place in-progress scratch data lives. It has no memory of
        # its own history; each write erases the previous one.
        write_json(WORKING_PATH, {
            "run_id": run_id,
            "current_step": step,
            "status": "in_progress",
            "scratch": {"computing_result_for_step": step},
        })
        print(f"  [working.json] overwritten -> current_step={step} (scratch only, no history kept here)")

        # Tier 2: durable log — append-only. Once a step is confirmed
        # complete, it is committed here and never rewritten.
        append_log({"event": "step_complete", "run_id": run_id, "step": step, "result": result})
        print(f"  [log.jsonl]     appended    -> step={step} result={result} (committed, permanent)")

        if crash_at is not None and step == crash_at:
            print(f"  !! SIMULATED CRASH after step {step} (run_id={run_id}) — process exits, working.json left dangling")
            sys.exit(1)

    write_json(WORKING_PATH, {"run_id": run_id, "current_step": STEPS, "status": "done", "scratch": {}})
    print(f"[run] run_id={run_id} completed all {STEPS} steps normally.")


def cmd_wipe_working():
    if os.path.exists(WORKING_PATH):
        os.remove(WORKING_PATH)
        print("[wipe-working] working.json deleted (simulates process death / container recycle).")
    else:
        print("[wipe-working] working.json did not exist — nothing to wipe.")


def cmd_reconstruct(run_id):
    print(f"[reconstruct] working.json present? {os.path.exists(WORKING_PATH)}")
    records = [r for r in read_log() if r.get("run_id") == run_id]
    if not records:
        print(f"[reconstruct] no durable log records found for run_id={run_id}.")
        return
    completed_steps = sorted(r["step"] for r in records)
    print(f"[reconstruct] recovered {len(records)} completed step(s) for run_id={run_id} from log.jsonl alone:")
    for r in records:
        print(f"    step {r['step']} -> result {r['result']}")
    last_known = max(completed_steps)
    print(f"[reconstruct] conclusion: last confirmed step = {last_known}/{STEPS}; "
          f"a resumer would restart at step {last_known + 1}. "
          f"No data was lost even though the ephemeral tier is gone.")


def cmd_blob_run(run_id, crash_at):
    print(f"[blob-run] starting run_id={run_id} using ANTI-PATTERN single blob.json (scratch + history merged)")
    history = []
    for step in range(1, STEPS + 1):
        result = step_result(run_id, step)
        history.append({"step": step, "result": result})
        # Everything -- current progress AND full history -- lives in ONE
        # object, in ONE file, with no append-only counterpart.
        write_json(BLOB_PATH, {
            "run_id": run_id,
            "current_step": step,
            "status": "in_progress",
            "history": history,
        })
        print(f"  [blob.json] overwritten -> current_step={step}, history now has {len(history)} entrie(s)")
        if crash_at is not None and step == crash_at:
            print(f"  !! SIMULATED CRASH after step {step} (run_id={run_id}) — blob.json is the only record of progress")
            sys.exit(1)
    write_json(BLOB_PATH, {"run_id": run_id, "current_step": STEPS, "status": "done", "history": history})
    print(f"[blob-run] run_id={run_id} completed all {STEPS} steps (still all in one file).")


def cmd_wipe_blob():
    had_it = os.path.exists(BLOB_PATH)
    if had_it:
        blob = read_json(BLOB_PATH, {})
        lost_steps = len(blob.get("history", []))
        os.remove(BLOB_PATH)
        print("[wipe-blob] blob.json deleted (same kind of process death as wipe-working).")
        print(f"[wipe-blob] conclusion: {lost_steps} previously-completed step result(s) are GONE. "
              f"There is no separate durable store to recover from, because scratch state and "
              f"history were never separated.")
    else:
        print("[wipe-blob] blob.json did not exist — nothing to wipe.")


def cmd_reset():
    removed = []
    for p in (WORKING_PATH, LOG_PATH, BLOB_PATH):
        if os.path.exists(p):
            os.remove(p)
            removed.append(os.path.basename(p))
    print(f"[reset] removed: {removed if removed else 'nothing (already clean)'}")


def parse_flag(args, name, cast=str, default=None):
    if name in args:
        idx = args.index(name)
        return cast(args[idx + 1])
    return default


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "run":
        run_id = parse_flag(args, "--run-id", str, "R1")
        crash_at = parse_flag(args, "--crash-at", int, None)
        cmd_run(run_id, crash_at)
    elif cmd == "wipe-working":
        cmd_wipe_working()
    elif cmd == "reconstruct":
        run_id = parse_flag(args, "--run-id", str, "R1")
        cmd_reconstruct(run_id)
    elif cmd == "blob-run":
        run_id = parse_flag(args, "--run-id", str, "R2")
        crash_at = parse_flag(args, "--crash-at", int, None)
        cmd_blob_run(run_id, crash_at)
    elif cmd == "wipe-blob":
        cmd_wipe_blob()
    elif cmd == "reset":
        cmd_reset()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
