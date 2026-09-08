"""
System under test: a keyword-based support-ticket router.

Deliberately tiny and deterministic — no network, no ML model, stdlib only.
It exists purely to give the observability harness (instrumented_run.py,
eval_harness.py) something with real steps, real inputs/outputs, and a real
tunable parameter (CONFIDENCE_THRESHOLD) to instrument and evaluate.

Pipeline: normalize -> tokenize -> score -> decide
Each function is a separate, independently-loggable step: one clear input,
one clear output, so a caller can wrap each in try/except + timing without
touching the logic inside.
"""

import re

CATEGORIES = {
    "billing": [
        "invoice", "charge", "payment", "refund", "subscription",
        "bill", "billed", "overcharged", "receipt",
    ],
    "technical": [
        "error", "crash", "bug", "login", "password", "broken",
        "freeze", "timeout", "500", "stacktrace",
    ],
    "account": [
        "account", "profile", "username", "delete", "email",
        "signup", "register", "settings",
    ],
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize(text):
    """Lowercase + strip. Raises if `text` is not a string (bad input)."""
    return text.lower().strip()


def tokenize(normalized_text):
    """Split into word tokens. Pure function of its input."""
    return _TOKEN_RE.findall(normalized_text)


def score(tokens):
    """
    Return {category: fraction_of_category_keywords_matched} for every
    category. Fraction, not raw count, so scores are comparable across
    categories with different keyword-list lengths and so a threshold in
    [0, 1] is meaningful.
    """
    token_set = set(tokens)
    scores = {}
    for category, keywords in CATEGORIES.items():
        hits = sum(1 for kw in keywords if kw in token_set)
        scores[category] = hits / len(keywords)
    return scores


def decide(scores, threshold):
    """
    Pick the highest-scoring category if it clears `threshold`, else
    "unknown". This is the ONE tunable variable the eval harness flips
    between runs.
    """
    best_category = max(scores, key=lambda c: scores[c])
    best_score = scores[best_category]
    if best_score >= threshold:
        return best_category, best_score
    return "unknown", best_score
