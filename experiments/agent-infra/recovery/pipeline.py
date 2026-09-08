"""Checkpointed pipeline.

Runs the 5 steps in steps.STEPS in order. After each step completes (i.e.
after its output has been atomically committed to disk), this process
appends the step's name to checkpoint.json and writes that checkpoint file
atomically too. On startup it reads checkpoint.json and skips any step
already listed as completed -- so a brand-new process (e.g. after a crash
and a restart) picks up exactly where the last one left off.

Usage: python3 pipeline.py
Env vars (for crash-injection testing, set by run.sh):
  CRASH_STEP=transform       -- crash partway through the named step
  CRASH_TRIGGER_FILE=<path>  -- touched right before this process expects
                                 to be killed, so an external driver knows
                                 when to send the SIGKILL
"""
import glob
import json
import os

from steps import STEPS, DATA_DIR, atomic_write_json, log

CHECKPOINT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoint.json")


def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH) as f:
            return json.load(f)
    return {"completed_steps": []}


def save_checkpoint(checkpoint):
    atomic_write_json(CHECKPOINT_PATH, checkpoint)


def clean_orphaned_temp_files():
    """A crash mid-step can leave a *.tmp.<pid> file behind: the side effect
    of a step that never got renamed into place. Nothing in the pipeline
    ever reads these (steps only ever read the final, committed path), so
    they are pure garbage. We remove them on startup just to keep the data
    directory tidy -- correctness does not depend on this cleanup running.
    """
    orphans = glob.glob(os.path.join(DATA_DIR, "*.tmp.*"))
    for path in orphans:
        log(f"STARTUP: found orphaned temp file from a half-done step -> {path} "
            f"(removing; the real output was never renamed to it, so nothing referenced it)")
        os.remove(path)
    if not orphans:
        log("STARTUP: no orphaned temp files found")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    clean_orphaned_temp_files()

    checkpoint = load_checkpoint()
    completed = set(checkpoint["completed_steps"])
    log(f"STARTUP: checkpoint shows completed steps = {sorted(completed) if completed else '[]'}")

    for name, func in STEPS:
        if name in completed:
            log(f"STEP {name}: SKIP (already completed per checkpoint)")
            continue
        func({})
        checkpoint["completed_steps"].append(name)
        save_checkpoint(checkpoint)
        log(f"CHECKPOINT: saved after completing '{name}' -> {checkpoint['completed_steps']}")

    log("PIPELINE COMPLETE")


if __name__ == "__main__":
    main()
