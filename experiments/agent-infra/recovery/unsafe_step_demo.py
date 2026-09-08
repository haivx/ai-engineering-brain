"""Demonstrates the cost of a NON-atomic step, for contrast against
steps.step_transform (which writes to a temp file and atomically renames).

This script writes directly to the final output path in two chunks, with
the process killed in between. Because there is no temp file and no atomic
rename, the kill leaves the real output file behind in a permanently
corrupted (truncated, invalid-JSON) state -- there is no "orphaned temp
file" here, the damage lands on the file that matters.

Usage: python3 unsafe_step_demo.py
Env var: CRASH_TRIGGER_FILE=<path> -- touched right before this process
expects to be killed.
"""
import os
import time

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unsafe_output.json")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    log("UNSAFE STEP: writing directly to the final path (no temp file, no atomic rename)")
    with open(OUT_PATH, "w") as f:
        f.write('{"values": [2, 4, 6, ')  # first chunk lands directly on the real file
        f.flush()
        os.fsync(f.fileno())
        log("UNSAFE STEP: first chunk committed straight to the REAL file; "
            "signaling driver and waiting to be killed")
        trigger = os.environ.get("CRASH_TRIGGER_FILE")
        if trigger:
            with open(trigger, "w") as tf:
                tf.write("ready")
        for _ in range(100):  # safety net only
            time.sleep(0.05)
        log("UNSAFE STEP: safety timeout, no external kill arrived; finishing write normally")
        f.write('8, 10]}')
    log("UNSAFE STEP: done")


if __name__ == "__main__":
    main()
