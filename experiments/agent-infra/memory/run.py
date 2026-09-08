#!/usr/bin/env python3
"""
Proof for concepts/agent-infra/memory.md — cross-RUN tiering:
session/plan state (dies at end of session) vs. durable log (never dies).

Two tiers, two files, on purpose:
  session.json — state for the CURRENT session only. A "session" here is a
                 short run of consecutive invocations of this script. It
                 accumulates facts across runs, then EXPIRES after
                 SESSION_MAX_RUNS runs. On expiry its accumulated facts are
                 promoted (summarized) into the durable log, and the file
                 itself is deleted -- a fresh session starts on the next run.
  log.jsonl    — append-only, durable across every run of every session,
                 forever. Nothing is ever removed from it by this script.

Determinism note: there is no wall-clock timestamp anywhere. The session id
is derived deterministically from how many "session_start" events already
exist in the durable log, so a clean `reset` + a fixed sequence of `run`
invocations always reproduces the same session ids and log contents.

Commands:
  python3 run.py run      # perform one run (create/continue/expire a session)
  python3 run.py show     # print current session.json + full log.jsonl
  python3 run.py reset    # wipe both tier files back to a clean slate
"""
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_PATH = os.path.join(BASE_DIR, "session.json")
LOG_PATH = os.path.join(BASE_DIR, "log.jsonl")

SESSION_MAX_RUNS = 2  # small on purpose, so 3 invocations are enough to see expiry


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


def next_session_id():
    starts = [r for r in read_log() if r.get("event") == "session_start"]
    return f"S{len(starts) + 1}"


def cmd_run():
    session = read_json(SESSION_PATH)

    if session is None:
        session_id = next_session_id()
        session = {"session_id": session_id, "run_count": 0, "facts": []}
        append_log({"event": "session_start", "session_id": session_id})
        print(f"[session] no session.json found -> starting new session {session_id}")
    else:
        session_id = session["session_id"]
        print(f"[session] continuing existing session {session_id} (run_count so far: {session['run_count']})")

    session["run_count"] += 1
    fact = f"fact-from-run-{session['run_count']}-of-{session_id}"
    session["facts"].append(fact)

    append_log({
        "event": "run",
        "session_id": session_id,
        "run_index": session["run_count"],
        "fact": fact,
    })
    print(f"[log.jsonl] appended durable 'run' event -> session={session_id} run_index={session['run_count']}")

    if session["run_count"] >= SESSION_MAX_RUNS:
        append_log({
            "event": "session_summary",
            "session_id": session_id,
            "total_runs": session["run_count"],
            "facts": session["facts"],
        })
        print(f"[log.jsonl] appended 'session_summary' -> session {session_id} reached "
              f"SESSION_MAX_RUNS={SESSION_MAX_RUNS}; facts promoted to durable log")
        os.remove(SESSION_PATH)
        print(f"[session] session.json DELETED — session {session_id}'s state no longer exists anywhere "
              f"except as the summary just promoted into log.jsonl")
    else:
        write_json(SESSION_PATH, session)
        print(f"[session.json] updated -> session={session_id} run_count={session['run_count']} "
              f"(still alive, will expire at run_count={SESSION_MAX_RUNS})")


def cmd_show():
    session = read_json(SESSION_PATH)
    print("=== session.json (session/plan state) ===")
    if session is None:
        print("  <absent — no active session right now>")
    else:
        print(json.dumps(session, indent=2, sort_keys=True))
    print("=== log.jsonl (durable log, all sessions, all runs) ===")
    records = read_log()
    if not records:
        print("  <empty>")
    for r in records:
        print(" ", json.dumps(r, sort_keys=True))
    print(f"=== totals: {len(records)} durable log record(s) ===")


def cmd_reset():
    removed = []
    for p in (SESSION_PATH, LOG_PATH):
        if os.path.exists(p):
            os.remove(p)
            removed.append(os.path.basename(p))
    print(f"[reset] removed: {removed if removed else 'nothing (already clean)'}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "run":
        cmd_run()
    elif cmd == "show":
        cmd_show()
    elif cmd == "reset":
        cmd_reset()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
