"""Task 10 — Demonstrate the system using the five sample customer queries.

Runs all five queries for a single customer ("David") so that the final
memory-recall query can retrieve an earlier issue from SQLite.

Refund (Query 4) is high-risk; the demo uses an auto-approve supervisor
callback so the run is non-interactive and reproducible for screenshots.
Run interactively instead with:  python main.py
"""
from __future__ import annotations

import os
import sys

# Ensure Unicode (e.g. arrows in the technical manual) prints on any console.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.config import DB_PATH
from src.graph import build_graph, handle_query
from src.hitl import make_auto_callback
from src import llm

CUSTOMER_ID = "CUST-DAVID"

SAMPLE_QUERIES = [
    ("What are the pricing plans available for your software?", "Sales"),
    ("I forgot my account password.", "Account"),
    ("My application crashes whenever I upload a file.", "Technical Support"),
    ("I need a refund for my annual subscription.", "Billing (human approval)"),
    ("What was my previous support issue?", "Memory recall (no routing)"),
]


def _print_result(idx: int, query: str, expected: str, state: dict) -> None:
    print("\n" + "=" * 74)
    print(f"QUERY {idx}: {query}")
    print(f"Expected path: {expected}")
    print("-" * 74)
    print(f"  Intent classified : {state.get('intent')}")
    print(f"  Department         : {state.get('department')}")
    print(f"  Risk category      : {state.get('risk_category')}")
    print(f"  Requires approval  : {state.get('requires_approval')}")
    print(f"  Approval status    : {state.get('approval_status')}")
    srcs = state.get("rag_sources") or []
    print(f"  RAG sources        : {', '.join(s.split('::')[0].strip() for s in srcs) or '(none)'}")
    print("  Workflow trace:")
    for step in state.get("trace", []):
        print(f"     -> {step}")
    print("-" * 74)
    print("  FINAL RESPONSE TO CUSTOMER:")
    for line in (state.get("final_response", "")).splitlines():
        print(f"  | {line}")


def run_demo(fresh: bool = True) -> None:
    if fresh and os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # reset memory for a reproducible demonstration

    print("#" * 74)
    print("  AI-POWERED CUSTOMER SUPPORT AUTOMATION SYSTEM  (LangGraph)")
    print(f"  LLM mode: {llm.provider().upper()}"
          f"{'  (deterministic, no API key needed)' if llm.is_offline() else ''}")
    print(f"  Customer: {CUSTOMER_ID}")
    print("#" * 74)

    # Auto-approve high-risk requests so the scripted demo runs unattended.
    app = build_graph(approval_callback=make_auto_callback("approved"))

    for i, (query, expected) in enumerate(SAMPLE_QUERIES, start=1):
        state = handle_query(app, CUSTOMER_ID, query)
        _print_result(i, query, expected, state)

    print("\n" + "#" * 74)
    print("  Demonstration complete. All interactions stored in:")
    print(f"  {DB_PATH}")
    print("#" * 74)


if __name__ == "__main__":
    run_demo()
