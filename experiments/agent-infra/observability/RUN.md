# RUN.md — captured terminal output

Environment: Python 3.9.6, stdlib only, run from this folder
(`experiments/agent-infra/observability/`). Every block below is the exact
stdout of the command shown above it (captured to a file and pasted in
verbatim, not retyped) — a one-line note above each says what it
demonstrates.

## 1. Baseline run (threshold = 0.0): structured log + eval score

Demonstrates: structured logging running underneath a real eval — every
step of every one of the 18 cases produced one JSONL record in
`logs/run_baseline.jsonl`, and the run still reduces to one number (66.7%)
up front.

```
$ python3 eval_harness.py --threshold 0.0 --tag baseline
run_id:        run-baseline-b02dafdf
tag:           baseline
threshold:     0.0
cases:         18
passed:        12
failed:        6
errored:       1
pass_rate:     66.7%
log:           logs/run_baseline.jsonl
result:        results/eval_baseline.json

case_id                      expected   predicted  pass   note
billing_invoice              billing    billing    PASS   
billing_generic              billing    billing    PASS   
billing_receipt              billing    billing    PASS   
billing_weak_single          billing    billing    PASS   
technical_login              technical  technical  PASS   
technical_timeout            technical  technical  PASS   
technical_password           technical  technical  PASS   
technical_weak_single        technical  technical  PASS   
account_profile              account    account    PASS   
account_signup               account    account    PASS   
account_delete               account    account    PASS   
account_weak_single          account    account    PASS   
unknown_greeting             unknown    billing    FAIL   
unknown_smalltalk            unknown    billing    FAIL   
unknown_incidental_delete    unknown    account    FAIL   
unknown_incidental_bill      unknown    billing    FAIL   
unknown_incidental_settings  unknown    account    FAIL   
malformed_none_input         None       None       FAIL   ERROR: AttributeError: 'NoneType' object has no attribute 'lower'
```

## 2. Changed run (threshold = 0.2): same cases, one variable changed

Demonstrates: only `--threshold` changed (0.0 -> 0.2). Same 18 cases, same
router.py, same code path, different outcomes on the near-threshold cases.

```
$ python3 eval_harness.py --threshold 0.2 --tag stricter
run_id:        run-stricter-97c9cd79
tag:           stricter
threshold:     0.2
cases:         18
passed:        14
failed:        4
errored:       1
pass_rate:     77.8%
log:           logs/run_stricter.jsonl
result:        results/eval_stricter.json

case_id                      expected   predicted  pass   note
billing_invoice              billing    billing    PASS   
billing_generic              billing    billing    PASS   
billing_receipt              billing    billing    PASS   
billing_weak_single          billing    unknown    FAIL   
technical_login              technical  technical  PASS   
technical_timeout            technical  technical  PASS   
technical_password           technical  technical  PASS   
technical_weak_single        technical  unknown    FAIL   
account_profile              account    account    PASS   
account_signup               account    account    PASS   
account_delete               account    account    PASS   
account_weak_single          account    unknown    FAIL   
unknown_greeting             unknown    unknown    PASS   
unknown_smalltalk            unknown    unknown    PASS   
unknown_incidental_delete    unknown    unknown    PASS   
unknown_incidental_bill      unknown    unknown    PASS   
unknown_incidental_settings  unknown    unknown    PASS   
malformed_none_input         None       None       FAIL   ERROR: AttributeError: 'NoneType' object has no attribute 'lower'
```

## 3. Before/after comparison: the number, not a feeling

Demonstrates: raising the confidence threshold from 0.0 to 0.2 net-improves
the pass rate (+11.1 points), but not for free — it trades 3 weak-signal
true positives (`*_weak_single`) for 5 corrected false positives on
genuinely off-topic input (`unknown_*`). The comparison table shows both
the net verdict AND the specific trade-off, from the numbers alone, with
no re-reading of the raw log required for this step.

```
$ python3 compare_runs.py --before baseline --after stricter
Comparing: baseline (threshold=0.0) -> stricter (threshold=0.2)

metric               before      after      delta
passed                   12         14         +2
failed                    6          4         -2
errored                   1          1         +0
pass_rate            66.7%     77.8%    +11.1%

Verdict: IMPROVED (+11.1% pass rate)

Per-case flips (8 of 18 cases changed outcome):
case_id                      direction      before_pred  after_pred   expected
billing_weak_single          PASS -> FAIL   billing      unknown      billing
technical_weak_single        PASS -> FAIL   technical    unknown      technical
account_weak_single          PASS -> FAIL   account      unknown      account
unknown_greeting             FAIL -> PASS   billing      unknown      unknown
unknown_smalltalk            FAIL -> PASS   billing      unknown      unknown
unknown_incidental_delete    FAIL -> PASS   account      unknown      unknown
unknown_incidental_bill      FAIL -> PASS   billing      unknown      unknown
unknown_incidental_settings  FAIL -> PASS   account      unknown      unknown
```

## 4. Reproducibility check: pass rate is stable across reruns

Demonstrates: no seeding was even needed here because the router has zero
randomness in its decision logic — pass_rate is bit-for-bit identical
across reruns. (`run_id` differs every run via `uuid.uuid4()`, but that's
an identifier for correlation, not part of the scored logic — the
constraint that "non-determinism must be seeded so pass-rate is stable"
is satisfied trivially by having none in the scored path.) The rerun
artifacts were deleted immediately after this check; they are not part of
the committed proof.

```
$ python3 eval_harness.py --threshold 0.0 --tag baseline_rerun > /dev/null 2>&1
$ python3 -c "... compare results/eval_baseline.json vs results/eval_baseline_rerun.json pass_rate ..."
baseline pass_rate: 0.6667
baseline_rerun pass_rate: 0.6667
REPRODUCIBLE
```

## 5. The real argument: localizing one failure in seconds

Both runs above show `malformed_none_input` failing with the same one-line
note: `ERROR: AttributeError: 'NoneType' object has no attribute 'lower'`.
That note only exists because the harness's console summary happens to
surface it. Two contrasts below show why the *structured log underneath*
is the part that actually matters, not the console print.

### 5a. What a bare pass-rate number tells you: nothing

Demonstrates: `naive_baseline_demo.py` runs the exact same 18 cases through
the exact same `router.py`, wrapped in one bare
`try/except Exception: print("case failed")`. It reaches the identical
12/18 score, but the six failures are indistinguishable: five are wrong
classifications, one is an outright crash on bad input, and this output
does not let you tell which is which, let alone which case_id or which
pipeline step. You'd have to go add prints and re-run to even discover the
crash exists as a distinct category of failure.

```
$ python3 naive_baseline_demo.py
case failed
case failed
case failed
case failed
case failed
case failed
12/18 passed
```

### 5b. What the structured log tells you: exact case, exact step, exact cause, in one grep

Demonstrates: one grep on `case_id` answers, in seconds, which case broke
(`malformed_none_input`), which pipeline step it broke in (`normalize`,
`step_seq: 1` — it never even reached `tokenize`/`score`/`decide`), the
exact exception, and that it took under 0.01ms to fail (so it's not a
hang). `status: "error"` also makes it mechanically distinguishable from
the five `status: "ok"` records for cases that ran clean but predicted the
wrong label — something neither `naive_baseline_demo.py`'s print output
nor a bare pass-rate number can tell apart.

```
$ grep '"case_id": "malformed_none_input"' logs/run_baseline.jsonl | python3 -m json.tool --json-lines
{
    "case_id": "malformed_none_input",
    "duration_ms": 0.0026,
    "error": "AttributeError: 'NoneType' object has no attribute 'lower'",
    "input": "None",
    "output": null,
    "run_id": "run-baseline-b02dafdf",
    "status": "error",
    "step": "normalize",
    "step_seq": 1,
    "timestamp": "2026-09-07T16:42:12.303277+00:00"
}
{
    "case_id": "malformed_none_input",
    "duration_ms": null,
    "error": "AttributeError: 'NoneType' object has no attribute 'lower'",
    "input": "None",
    "output": "{'case_id': 'malformed_none_input', 'expected': None, 'predicted': None, 'confidence': None, 'passed': False, 'errored': True, 'failed_step': 'normalize', 'error': \"AttributeError: 'NoneType' object h...<truncated>",
    "run_id": "run-baseline-b02dafdf",
    "status": "error",
    "step": "case_result",
    "step_seq": 2,
    "timestamp": "2026-09-07T16:42:12.303292+00:00"
}
```

## 6. Files this run produced

```
$ wc -l logs/run_baseline.jsonl logs/run_stricter.jsonl
      88 logs/run_baseline.jsonl
      88 logs/run_stricter.jsonl
     176 total
```

88 records per run = 17 clean cases x 5 records each (normalize, tokenize,
score, decide, case_result) = 85, + 1 malformed case x 2 records
(normalize error, case_result) = 87, + 1 run_summary record = 88.

Other files in this folder: `router.py` (system under test),
`eval_harness.py` (structured logger + eval runner), `compare_runs.py`
(before/after diff), `naive_baseline_demo.py` (contrast piece for §5a),
`eval_cases.json` (18 cases), `logs/run_baseline.jsonl` /
`logs/run_stricter.jsonl` (structured logs), `results/eval_baseline.json`
/ `results/eval_stricter.json` (eval summaries + per-case outcomes).
