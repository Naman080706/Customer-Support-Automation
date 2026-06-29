"""Interactive CLI for the Customer Support Automation System.

Usage:
    python main.py                 # interactive chat (asks for customer id)
    python main.py --demo          # run the 5-query demonstration (Task 10)

High-risk requests pause for a real supervisor decision at the console.
"""
from __future__ import annotations

import argparse
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src import llm
from src.graph import build_graph, handle_query


def interactive() -> None:
    print("=" * 70)
    print(" AI-Powered Customer Support Automation System (LangGraph)")
    print(f" LLM mode: {llm.provider().upper()}")
    print(" Type 'quit' to exit.")
    print("=" * 70)

    customer_id = input("Enter customer id (e.g. CUST-DAVID): ").strip() or "CUST-GUEST"
    app = build_graph()  # console approval prompt for high-risk requests

    while True:
        query = input(f"\n[{customer_id}] You: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not query:
            continue
        state = handle_query(app, customer_id, query)
        print(f"\nAssistant ({state.get('department')}):")
        print(state.get("final_response", ""))
        print(
            f"\n[intent={state.get('intent')} | approval={state.get('approval_status')} "
            f"| rag={len(state.get('rag_sources') or [])} source(s)]"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Customer Support Automation System")
    parser.add_argument("--demo", action="store_true", help="Run the 5-query demo")
    args = parser.parse_args()
    if args.demo:
        from demo import run_demo
        run_demo()
    else:
        interactive()


if __name__ == "__main__":
    main()
