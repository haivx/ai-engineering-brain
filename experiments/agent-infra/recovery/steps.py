"""Shared step implementations for the checkpoint/resume experiment.

Each step is a pure function of the previous step's output file(s): given
the same input on disk, it always produces the same output. Every step
commits its output *atomically* -- it writes to a private temp file first,
then uses os.replace() (an atomic rename on POSIX) to publish it under the
real path. That is deliberate: a crash can only ever leave behind an
orphaned temp file. The real output path is untouched until the rename
succeeds, so re-running a half-done step from scratch is always safe.

steps.py has no opinion about checkpointing -- pipeline.py (checkpointed)
and no_checkpoint_pipeline.py (baseline, no checkpointing) both import this
module and just differ in whether they skip steps a checkpoint says are
already done.
"""
import json
import os
import sys
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def atomic_write_json(path, obj):
    tmp_path = f"{path}.tmp.{os.getpid()}"
    with open(tmp_path, "w") as f:
        json.dump(obj, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)  # atomic on POSIX: readers never see a partial file


def read_json(path):
    with open(path) as f:
        return json.load(f)


def maybe_crash(step_name):
    """Crash-injection hook. If the CRASH_STEP env var names this step, we
    have already written a side effect to disk (a temp file) by the time
    this is called. We touch CRASH_TRIGGER_FILE to tell the external driver
    "a side effect has started, kill me now" and then just wait to be
    SIGKILLed. The sleep loop is a safety net only, in case nobody kills us.
    """
    if os.environ.get("CRASH_STEP") != step_name:
        return
    trigger = os.environ.get("CRASH_TRIGGER_FILE")
    log(f"CRASH-INJECT[{step_name}]: side effect (temp file) written to disk; "
        f"signaling driver via trigger file and waiting to be killed")
    if trigger:
        with open(trigger, "w") as tf:
            tf.write("ready")
    for _ in range(100):  # ~5s safety net
        time.sleep(0.05)
    log(f"CRASH-INJECT[{step_name}]: safety timeout, no external kill arrived; exiting nonzero")
    sys.exit(99)


def step_fetch_input(ctx):
    log("STEP fetch_input: starting")
    result = {"values": [1, 2, 3, 4, 5], "source": "synthetic"}
    out_path = os.path.join(DATA_DIR, "step1_input.json")
    atomic_write_json(out_path, result)
    log(f"STEP fetch_input: committed -> {out_path}")
    return result


def step_validate(ctx):
    log("STEP validate: starting")
    data = read_json(os.path.join(DATA_DIR, "step1_input.json"))
    assert all(isinstance(v, int) for v in data["values"]), "validation failed"
    result = {"values": data["values"], "validated": True}
    out_path = os.path.join(DATA_DIR, "step2_validated.json")
    atomic_write_json(out_path, result)
    log(f"STEP validate: committed -> {out_path}")
    return result


def step_transform(ctx):
    """This is the step the experiment crashes mid-way through: a temp file
    is written (the side effect / half-done state), then -- before the
    atomic rename that would commit it -- maybe_crash() can land an external
    SIGKILL here.
    """
    log("STEP transform: starting")
    data = read_json(os.path.join(DATA_DIR, "step2_validated.json"))
    transformed = {"values": [v * 2 for v in data["values"]]}
    out_path = os.path.join(DATA_DIR, "step3_transformed.json")
    tmp_path = f"{out_path}.tmp.{os.getpid()}"
    with open(tmp_path, "w") as f:
        json.dump(transformed, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    log(f"STEP transform: side effect written to temp file {tmp_path} (not yet committed)")
    maybe_crash("transform")  # <-- crash-injection point: after side effect, before commit
    os.replace(tmp_path, out_path)
    log(f"STEP transform: committed -> {out_path}")
    return transformed


def step_aggregate(ctx):
    log("STEP aggregate: starting")
    data = read_json(os.path.join(DATA_DIR, "step3_transformed.json"))
    result = {"sum": sum(data["values"]), "count": len(data["values"])}
    out_path = os.path.join(DATA_DIR, "step4_aggregated.json")
    atomic_write_json(out_path, result)
    log(f"STEP aggregate: committed -> {out_path}")
    return result


def step_write_report(ctx):
    log("STEP write_report: starting")
    data = read_json(os.path.join(DATA_DIR, "step4_aggregated.json"))
    result = {"report": f"sum={data['sum']} count={data['count']}", "final": True}
    out_path = os.path.join(DATA_DIR, "step5_report.json")
    atomic_write_json(out_path, result)
    log(f"STEP write_report: committed -> {out_path}")
    return result


STEPS = [
    ("fetch_input", step_fetch_input),
    ("validate", step_validate),
    ("transform", step_transform),
    ("aggregate", step_aggregate),
    ("write_report", step_write_report),
]
