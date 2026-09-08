#!/usr/bin/env python3
"""
Proof for concepts/agent-infra/determinism.md — the non-deterministic
boundary, isolated behind ONE function with a stated input/output contract.

Everything in this file EXCEPT `non_deterministic_call` (and, opt-in,
`live_llm_call`) is pure: no randomness, no wall clock, no I/O side effects,
no reliance on incidental iteration order. Given the same arguments they
return the same value, forever.

    assemble_input()  -- deterministic: builds the canonical prompt
    non_deterministic_call() -- THE boundary. One function. Contract:
        in:  canonical_prompt: str
        out: {"raw_text": str, "raw_confidence": float, "latency_ms": int}
        Uses the process-global `random` module WITHOUT a fixed seed, and
        `time` for latency — standing in for real LLM sampling variance /
        network jitter. This is the ONLY place in the file allowed to do that.
    parse_output()    -- deterministic: extracts a structured label from
                          raw_text by looking for the word "approve".
    decide()          -- deterministic: pure function of the parsed label.
    run_pipeline()     -- wires the above together and returns a structured
                          log split into a `deterministic` section and an
                          `nd` (non-deterministic) section, on purpose kept
                          as two separate objects rather than merged, so a
                          caller can diff/compare each half independently.

`run_pipeline` takes `boundary_fn` as a parameter (default
`non_deterministic_call`) purely so record_replay.py can swap in a fixture
without touching this module — that's the record/replay hook.

Stub simplification (documented, not hidden): the fake "LLM" bakes its true
verdict into the prompt content (the word "urgent" => APPROVE) so the
underlying decision is well-posed and recoverable regardless of phrasing.
What varies run-to-run is *how* it's worded, its self-reported confidence,
and its latency — exactly the kind of variance real sampling produces on an
easy, low-ambiguity question. This is a teaching stub, not a claim about
real LLM statistics.
"""
import os
import random
import time
import urllib.request
import urllib.error
import json as _json

APPROVE_TEMPLATES = [
    "Yes, approve — the request meets policy.",
    "Approved. This satisfies the policy requirements.",
    "This should be approved; it is policy-compliant.",
    "Approve. Nothing here violates policy.",
]
REJECT_TEMPLATES = [
    "No, reject — this does not meet policy.",
    "Rejected. The request violates policy.",
    "This should be rejected; it fails the policy check.",
    "Reject. This is not policy-compliant.",
]


def assemble_input(user_request):
    """Deterministic. Canonical, sorted-key, fixed-format prompt string."""
    lines = ["{}: {}".format(k, user_request[k]) for k in sorted(user_request)]
    return "REQUEST\n" + "\n".join(lines)


def non_deterministic_call(canonical_prompt):
    """THE non-deterministic boundary. See module docstring for contract.

    Ground truth is deterministic (baked into the prompt) so the *label*
    is recoverable; wording/confidence/latency are not.
    """
    label = "APPROVE" if "urgent" in canonical_prompt.lower() else "REJECT"
    templates = APPROVE_TEMPLATES if label == "APPROVE" else REJECT_TEMPLATES
    text = random.choice(templates)               # unseeded -> varies per run
    confidence = round(random.uniform(0.75, 0.99), 3)  # unseeded -> varies per run
    latency_ms = random.randint(120, 480)          # stands in for network jitter
    time.sleep(0)  # no real delay; latency_ms above is the simulated figure
    return {"raw_text": text, "raw_confidence": confidence, "latency_ms": latency_ms}


def live_llm_call(canonical_prompt, model="meta-llama/llama-3.1-8b-instruct"):
    """OPTIONAL real-LLM path for the same boundary contract. OFF by default.

    Only used if a caller explicitly opts in (--live flag in run_stable.py)
    AND OPENROUTER_API_KEY is set in the environment. Never prints the key.
    Falls back to the stub (with a warning on stderr) on any error so the
    rest of the proof never depends on network access.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set; cannot make a live call")
    body = _json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": canonical_prompt}],
        "temperature": 1.0,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": "Bearer {}".format(api_key),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = _json.loads(resp.read().decode("utf-8"))
    latency_ms = int((time.time() - start) * 1000)
    text = payload["choices"][0]["message"]["content"]
    return {"raw_text": text, "raw_confidence": None, "latency_ms": latency_ms}


def parse_output(boundary_output):
    """Deterministic. Same raw_text always yields the same label."""
    text = boundary_output["raw_text"].lower()
    label = "APPROVE" if "approve" in text else "REJECT"
    return {"label": label}


def decide(parsed):
    """Deterministic. Pure function of the parsed label, nothing else."""
    if parsed["label"] == "APPROVE":
        return {"action": "grant_access", "reason": "model approved request"}
    return {"action": "deny_access", "reason": "model rejected request"}


def run_pipeline(user_request, boundary_fn=non_deterministic_call):
    """Wire the stages together. Returns (decision, log) where log has two
    keys kept separate on purpose: 'deterministic' and 'nd'.
    """
    prompt = assemble_input(user_request)
    boundary_out = boundary_fn(prompt)
    parsed = parse_output(boundary_out)
    decision = decide(parsed)

    log = {
        "deterministic": {
            "assemble_input": prompt,
            "parse_output": parsed,
            "decide": decision,
        },
        "nd": {
            "boundary_call": boundary_out,
        },
    }
    return decision, log


def canonical_json(obj):
    """Deterministic serialization used everywhere logs are compared/written."""
    return _json.dumps(obj, sort_keys=True, indent=2)
