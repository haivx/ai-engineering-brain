#!/bin/bash
# Driver for the checkpoint/resume experiment. Launches pipeline.py as a
# real subprocess, waits for it to signal that a side effect has started,
# then sends it a genuine SIGKILL -- this is a real process kill, not a
# simulated one inside a single continuous run. It then launches a brand
# new process to prove resumption, and compares results against an
# uninterrupted happy-path run.
set -uo pipefail
cd "$(dirname "$0")"

md5_of() {
  if command -v md5 >/dev/null 2>&1; then
    md5 -q "$1"
  else
    md5sum "$1" | awk '{print $1}'
  fi
}

section() { echo; echo "==== $1 ===="; }

clean_all() {
  rm -rf data checkpoint.json crash_trigger unsafe_output.json \
    run1.log run2.log run3.log run4.log run5.log baseline_report.json
}

wait_for_trigger_then_kill() {
  # $1 = pid, $2 = trigger file path
  local pid="$1" trigger="$2" i
  for i in $(seq 1 200); do
    [ -f "$trigger" ] && break
    sleep 0.05
  done
  if [ -f "$trigger" ]; then
    echo "trigger file observed -> sending SIGKILL to PID $pid now"
    kill -9 "$pid" 2>/dev/null
  else
    echo "WARNING: trigger file never appeared within timeout; not killing"
  fi
  wait "$pid" 2>/dev/null
  echo "process exit status after kill: $?"
}

section "1. CLEAN SLATE"
clean_all
ls -la

section "2. UNINTERRUPTED HAPPY-PATH RUN (baseline for comparison)"
python3 pipeline.py
cp data/step5_report.json baseline_report.json
echo "--- baseline final report ---"
cat baseline_report.json
BASELINE_MD5=$(md5_of baseline_report.json)
echo "baseline md5: $BASELINE_MD5"

section "3. CLEAN SLATE FOR CRASH SCENARIO"
clean_all
ls -la

section "4. LAUNCH CHECKPOINTED PIPELINE, INJECT REAL SIGKILL MID 'transform' STEP"
export CRASH_STEP=transform
export CRASH_TRIGGER_FILE="$(pwd)/crash_trigger"
rm -f "$CRASH_TRIGGER_FILE"
python3 pipeline.py > run1.log 2>&1 &
PID=$!
echo "launched pipeline.py as PID $PID"
wait_for_trigger_then_kill "$PID" "$CRASH_TRIGGER_FILE"
unset CRASH_STEP CRASH_TRIGGER_FILE
echo "--- run1.log (first process; killed mid 'transform') ---"
cat run1.log

section "5. ON-DISK STATE AFTER THE KILL, BEFORE ANY RESTART"
echo "checkpoint.json:"
cat checkpoint.json
echo
echo "data/ listing (note the orphaned step3_transformed.json.tmp.* file -- the half-done step):"
ls -la data/

section "6. RESTART: BRAND NEW PROCESS RESUMES FROM LAST CHECKPOINT"
python3 pipeline.py > run2.log 2>&1
echo "--- run2.log (second, new process; resumes) ---"
cat run2.log

section "7. VERIFY: RESUMED RESULT == UNINTERRUPTED HAPPY-PATH RESULT"
echo "--- resumed final report ---"
cat data/step5_report.json
RESUMED_MD5=$(md5_of data/step5_report.json)
echo "baseline md5: $BASELINE_MD5"
echo "resumed  md5: $RESUMED_MD5"
if [ "$BASELINE_MD5" = "$RESUMED_MD5" ]; then
  echo "RESULT: MATCH -- resumed run produced byte-identical output to the uninterrupted run"
else
  echo "RESULT: MISMATCH -- investigate"
fi

section "8. CONTRAST: NO-CHECKPOINT BASELINE, SAME CRASH, RESTARTS FROM ZERO"
rm -rf data checkpoint.json
export CRASH_STEP=transform
export CRASH_TRIGGER_FILE="$(pwd)/crash_trigger"
rm -f "$CRASH_TRIGGER_FILE"
python3 no_checkpoint_pipeline.py > run3.log 2>&1 &
PID=$!
echo "launched no_checkpoint_pipeline.py as PID $PID"
wait_for_trigger_then_kill "$PID" "$CRASH_TRIGGER_FILE"
unset CRASH_STEP CRASH_TRIGGER_FILE
echo "--- run3.log (no-checkpoint, first process; killed mid 'transform') ---"
cat run3.log

echo
echo "restarting no-checkpoint pipeline..."
python3 no_checkpoint_pipeline.py > run4.log 2>&1
echo "--- run4.log (no-checkpoint, restart -- note fetch_input and validate re-run too) ---"
cat run4.log

section "9. COST OF A NON-ATOMIC STEP: SAME KIND OF KILL, NO TEMP+RENAME"
rm -f unsafe_output.json crash_trigger
export CRASH_TRIGGER_FILE="$(pwd)/crash_trigger"
python3 unsafe_step_demo.py > run5.log 2>&1 &
PID=$!
echo "launched unsafe_step_demo.py as PID $PID"
wait_for_trigger_then_kill "$PID" "$CRASH_TRIGGER_FILE"
unset CRASH_TRIGGER_FILE
echo "--- run5.log ---"
cat run5.log
echo
echo "unsafe_output.json contents (expect truncated / invalid JSON, permanently):"
cat unsafe_output.json
echo
echo
python3 -c "import json; json.load(open('unsafe_output.json'))" 2>/dev/null \
  && echo "JSON parsed OK (unexpected)" \
  || echo "JSON PARSE FAILED as expected: the real file was corrupted by a non-atomic write + kill, and nothing in this design would ever fix it -- unlike steps.py's temp+rename, which never touches the real path until it's whole"

# crash_trigger is a driver-only signaling file (the crashing child touches
# it to tell us "kill me now"); it has no meaning once this script exits, so
# clean it up rather than leaving unexplained IPC residue on disk.
rm -f "$(pwd)/crash_trigger"

section "DONE"
