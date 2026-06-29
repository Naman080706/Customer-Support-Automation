"""Task 4 — Conditional routing.

Directs a query to the appropriate node based on the classified intent. Memory
recall queries skip department routing entirely (per Query 5).
"""
from __future__ import annotations

from .state import SupportState

# Maps an intent label to the graph node that handles it.
INTENT_TO_NODE = {
    "Sales": "sales_agent",
    "Technical": "technical_agent",
    "Billing": "billing_agent",
    "Account": "account_agent",
    "Memory": "memory_recall",
}


def route_query(state: SupportState) -> str:
    """Return the next node name for LangGraph's conditional edges."""
    if state.get("is_memory_query"):
        return "memory_recall"
    intent = state.get("intent", "Sales")
    return INTENT_TO_NODE.get(intent, "sales_agent")
