from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Blocker:
    kind: str
    summary: str


PATTERNS = {
    "quota_exhausted": (
        "quota",
        "usage limit",
        "credit balance",
        "billing hard limit",
        "insufficient_quota",
        "monthly limit",
    ),
    "rate_limited": (
        "rate limit",
        "rate_limit",
        "too many requests",
        "429",
        "temporarily unavailable",
    ),
    "context_limited": (
        "context length",
        "context window",
        "maximum context",
        "too many tokens",
        "token limit",
        "exceeds the context",
        "context_length_exceeded",
    ),
    "auth_required": (
        "unauthorized",
        "invalid api key",
        "authentication",
        "not logged in",
        "login required",
        "please login",
    ),
    "token_budget": (
        "token budget",
        "budget exceeded",
        "out of tokens",
        "tokens exhausted",
    ),
}


SUMMARIES = {
    "quota_exhausted": "Agent quota or paid usage limit is exhausted. Refill/upgrade/wait for reset, then rerun this task.",
    "rate_limited": "Agent API is rate limited. Wait for the provider window to reset, then rerun this task.",
    "context_limited": "Agent hit a context/token limit. Split or compact the task before rerunning.",
    "auth_required": "Agent authentication is missing or expired. Re-login or update the token, then rerun.",
    "token_budget": "Configured token budget is exhausted. Increase the budget or switch to a cheaper model, then rerun.",
    "cli_failed": "Agent CLI failed. Check the recent output and rerun after fixing the blocker.",
}


def classify_blocker(output: str, returncode: int | None = None) -> Blocker:
    text = output.lower()
    for kind, patterns in PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            return Blocker(kind, SUMMARIES[kind])
    if returncode is None:
        return Blocker("cli_failed", SUMMARIES["cli_failed"])
    return Blocker("cli_failed", f"{SUMMARIES['cli_failed']} Exit code: {returncode}.")
