"""Task 2 — State structure for the Customer Support Automation System.

The graph state carries everything a request needs as it flows through the
LangGraph workflow: customer information, query details, retrieved context,
approval status, and the responses produced along the way.
"""
from __future__ import annotations

from typing import List, Optional, TypedDict


class SupportState(TypedDict, total=False):
    # --- Customer information ---
    customer_id: str             # stable id used as the memory/thread key
    customer_name: Optional[str] # extracted from the message if provided

    # --- Query details ---
    query: str                   # the raw customer message
    intent: Optional[str]        # Sales | Technical | Billing | Account | Memory
    department: Optional[str]    # human-readable department label
    risk_category: Optional[str] # refund | account_closure | ... | none
    is_memory_query: bool        # True for "what was my previous issue?"

    # --- Retrieved context (RAG + memory) ---
    retrieved_context: List[str] # snippets returned by the RAG pipeline
    rag_sources: List[str]       # source document names for the snippets
    memory_context: str          # summary of prior interactions from SQLite

    # --- Human-in-the-loop approval ---
    requires_approval: bool      # True for high-risk requests
    approval_status: str         # not_required | pending | approved | rejected
    approver: Optional[str]      # who approved/rejected (supervisor id)

    # --- Responses ---
    agent_response: str          # draft produced by the department agent
    final_response: str          # supervisor-validated response sent to customer

    # --- Bookkeeping ---
    trace: List[str]             # ordered log of nodes visited (for screenshots)


def new_state(customer_id: str, query: str) -> SupportState:
    """Create a fresh state for an incoming customer query."""
    return SupportState(
        customer_id=customer_id,
        customer_name=None,
        query=query,
        intent=None,
        department=None,
        risk_category="none",
        is_memory_query=False,
        retrieved_context=[],
        rag_sources=[],
        memory_context="",
        requires_approval=False,
        approval_status="not_required",
        approver=None,
        agent_response="",
        final_response="",
        trace=[],
    )
