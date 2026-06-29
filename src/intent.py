"""Task 3 — Intent Classification node.

Categorizes a customer query into one of:
    Sales | Technical | Billing | Account | Memory

It also detects a *risk category* (refund, account closure, ...) used later by
the human-in-the-loop node. Classification uses the LLM when a key is present,
otherwise a deterministic keyword classifier (so it always runs offline).
"""
from __future__ import annotations

import re
from typing import Tuple

from . import llm
from .state import SupportState

VALID_INTENTS = {"Sales", "Technical", "Billing", "Account", "Memory"}

# Keyword signals per intent (offline classifier).
_KEYWORDS = {
    "Sales": [
        "price", "pricing", "plan", "plans", "cost", "subscription", "upgrade",
        "discount", "trial", "buy", "purchase", "quote", "features", "tier",
        "enterprise", "starter", "professional",
    ],
    "Technical": [
        "error", "crash", "crashes", "bug", "install", "installation", "login",
        "log in", "password reset link", "configuration", "configure", "setup",
        "sync", "upload", "not working", "broken", "fails", "failed", "2fa",
        "freeze", "slow", "diagnostic",
    ],
    "Billing": [
        "invoice", "payment", "refund", "charge", "charged", "billing", "bill",
        "card", "receipt", "money", "overcharged", "credit", "compensation",
    ],
    "Account": [
        "password", "profile", "account", "activate", "activation",
        "deactivate", "deactivation", "username", "email address", "close my",
        "closure", "delete my account", "reset",
    ],
}

# Memory-recall signals (Query 5: "What was my previous support issue?")
_MEMORY_SIGNALS = [
    "previous issue", "previous support", "last issue", "earlier issue",
    "what was my", "remember", "what did i", "my last", "told you before",
    "prior issue", "past issue", "remind me what",
]

# Risk categories -> trigger phrases (drives human-in-the-loop).
_RISK_PATTERNS = {
    "refund": ["refund", "money back", "reimburse"],
    "subscription_cancellation": [
        "cancel my subscription", "cancel subscription", "cancel my plan",
        "cancel plan", "end my subscription", "stop my subscription",
    ],
    "account_closure": [
        "close my account", "account closure", "delete my account",
        "terminate my account", "shut down my account",
    ],
    "compensation": ["compensation", "service credit", "credit my account", "compensate"],
    "escalation": ["escalate", "speak to a manager", "talk to management", "supervisor"],
}


def detect_risk_category(query: str) -> str:
    q = query.lower()
    for category, phrases in _RISK_PATTERNS.items():
        if any(p in q for p in phrases):
            return category
    return "none"


def _is_memory_query(query: str) -> bool:
    q = query.lower()
    return any(sig in q for sig in _MEMORY_SIGNALS)


def extract_name(query: str):
    """Best-effort extraction of 'My name is X' for memory personalization."""
    m = re.search(r"\bmy name is\s+([A-Z][a-zA-Z]+)", query, re.IGNORECASE)
    if m:
        return m.group(1).capitalize()
    m = re.search(r"\bi am\s+([A-Z][a-zA-Z]+)\b", query)
    if m:
        return m.group(1).capitalize()
    return None


def _keyword_classify(query: str) -> str:
    q = query.lower()
    scores = {intent: 0 for intent in _KEYWORDS}
    for intent, words in _KEYWORDS.items():
        for w in words:
            if w in q:
                scores[intent] += 1
    # Refund/compensation are billing matters even if "account" appears.
    risk = detect_risk_category(query)
    if risk in ("refund", "compensation"):
        scores["Billing"] += 2
    if risk == "subscription_cancellation":
        scores["Billing"] += 1
    if risk == "account_closure":
        scores["Account"] += 2

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Sales"  # safe default: general product questions
    return best


def _llm_classify(query: str) -> str:
    system = (
        "You are an intent classifier for a SaaS customer support system. "
        "Classify the customer query into exactly one of these labels: "
        "Sales, Technical, Billing, Account. "
        "Reply with ONLY the single label word."
    )
    out = llm.generate(system, f"Customer query: {query}")
    if out:
        for intent in ("Sales", "Technical", "Billing", "Account"):
            if intent.lower() in out.lower():
                return intent
    return _keyword_classify(query)


def classify_intent(state: SupportState) -> SupportState:
    """LangGraph node: populate intent, risk_category, memory flag, name."""
    query = state["query"]
    trace = list(state.get("trace", []))

    name = extract_name(query)
    if name:
        state["customer_name"] = name

    if _is_memory_query(query):
        state["is_memory_query"] = True
        state["intent"] = "Memory"
        state["department"] = "Memory Recall"
        state["risk_category"] = "none"
        trace.append("intent: Memory (memory-recall query)")
        state["trace"] = trace
        return state

    intent = _llm_classify(query) if not llm.is_offline() else _keyword_classify(query)
    if intent not in VALID_INTENTS:
        intent = "Sales"

    state["intent"] = intent
    state["risk_category"] = detect_risk_category(query)
    trace.append(
        f"intent: {intent} | risk: {state['risk_category']} "
        f"| engine: {'llm:'+llm.provider() if not llm.is_offline() else 'rule-based'}"
    )
    state["trace"] = trace
    return state
