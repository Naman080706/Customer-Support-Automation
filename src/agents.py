"""Task 5 — Specialized support agents.

One agent per department: Sales, Technical, Billing, Account. Each agent:
  1. Retrieves relevant context from the knowledge base (RAG, Task 6).
  2. Drafts a grounded response (LLM if available, deterministic otherwise).

The draft is stored in state["agent_response"] and later validated/improved by
the Supervisor agent (Task 9) before being sent to the customer.
"""
from __future__ import annotations

from . import llm
from .config import DEPARTMENT_LABELS
from .rag import get_pipeline
from .state import SupportState

# Persona / tone guidance per department (used in both LLM and offline modes).
_PERSONAS = {
    "Sales": "a friendly Sales specialist helping with plans, pricing and features",
    "Technical": "a precise Technical Support engineer solving errors and setup issues",
    "Billing": "a careful Billing specialist handling invoices, payments and refunds",
    "Account": "a helpful Account specialist handling passwords, profiles and account status",
}


def _draft_with_llm(department: str, query: str, context: str) -> str | None:
    system = (
        f"You are {_PERSONAS[department]} at ABC Technologies. "
        "Answer the customer's query using ONLY the provided company context. "
        "Be concise, accurate and helpful. If the context lacks the answer, say "
        "you will route them to a human specialist."
    )
    user = f"Company context:\n{context}\n\nCustomer query: {query}"
    return llm.generate(system, user)


def _draft_offline(department: str, query: str, snippets: list[str]) -> str:
    """Deterministic, grounded response built from retrieved KB snippets."""
    label = DEPARTMENT_LABELS[department]
    if snippets:
        # Use the single most relevant snippet, trimmed, as the grounded core.
        core = snippets[0].strip()
        # Keep it readable: first ~6 non-empty lines of the top chunk.
        lines = [ln.strip() for ln in core.splitlines() if ln.strip()]
        body = "\n".join(lines[:8])
        return (
            f"[{label}] Thanks for reaching out. Based on our records:\n\n"
            f"{body}\n\n"
            f"If you need anything else regarding this, the {label} team is happy to help."
        )
    return (
        f"[{label}] Thanks for contacting ABC Technologies. I could not find an "
        f"exact match in our documents, so I'm routing you to a {label} specialist "
        f"who will follow up shortly."
    )


def _run_agent(department: str, state: SupportState) -> SupportState:
    query = state["query"]
    trace = list(state.get("trace", []))

    # --- Task 6: RAG retrieval ---
    snippets, sources = get_pipeline().retrieve_context(query, k=3)
    state["retrieved_context"] = snippets
    state["rag_sources"] = sources

    # --- Draft response ---
    context_blob = "\n\n".join(snippets) if snippets else "(no relevant document found)"
    draft = None
    if not llm.is_offline():
        draft = _draft_with_llm(department, query, context_blob)
    if not draft:
        draft = _draft_offline(department, query, snippets)

    state["agent_response"] = draft
    state["department"] = DEPARTMENT_LABELS[department]
    trace.append(
        f"agent: {DEPARTMENT_LABELS[department]} | rag_hits: {len(snippets)} "
        f"| sources: {', '.join(s.split('::')[0].strip() for s in sources) or 'none'}"
    )
    state["trace"] = trace
    return state


# --- LangGraph nodes (one per department) ----------------------------------
def sales_agent(state: SupportState) -> SupportState:
    return _run_agent("Sales", state)


def technical_agent(state: SupportState) -> SupportState:
    return _run_agent("Technical", state)


def billing_agent(state: SupportState) -> SupportState:
    return _run_agent("Billing", state)


def account_agent(state: SupportState) -> SupportState:
    return _run_agent("Account", state)
