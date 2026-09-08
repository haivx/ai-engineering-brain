"""Baseline with NO checkpointing, for contrast against pipeline.py.

Runs the exact same 5 steps, but never reads or writes any checkpoint file.
Every invocation of this script re-runs every step from scratch, regardless
of what a previous (possibly crashed) invocation already finished. This is
the "restart from zero" failure mode that checkpointing exists to avoid.

Usage: python3 no_checkpoint_pipeline.py
Env vars: same CRASH_STEP / CRASH_TRIGGER_FILE as pipeline.py.
"""
import os

from steps import STEPS, DATA_DIR, log


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    log("STARTUP: no checkpoint file is ever read -- always starting at step 1")
    for name, func in STEPS:
        log(f"STEP {name}: running (no checkpoint to skip against)")
        func({})
    log("PIPELINE COMPLETE")


if __name__ == "__main__":
    main()
