"""Task 9 — Supervisor agent.

Validates and improves the department agent's draft before it is sent to the
customer: it polishes tone, adds a courteous greeting/closing, appends approval
context for high-risk requests, and produces the final response.
"""
from __future__ import annotations

from . import llm
from .state import SupportState


def _improve_with_llm(state: SupportState) -> str | None:
    system = (
        "You are a senior support Supervisor at ABC Technologies. Improve the "
        "draft response below for clarity, correctness, empathy and professional "
        "tone. Keep all factual content from the draft and the company context. "
        "Return only the improved customer-facing message."
    )
    user = (
        f"Customer query: {state['query']}\n"
        f"Department: {state.get('department')}\n"
        f"Approval status: {state.get('approval_status')}\n\n"
        f"Draft response:\n{state.get('agent_response', '')}"
    )
    return llm.generate(system, user)


def _improve_offline(state: SupportState) -> str:
    name = state.get("customer_name")
    greeting = f"Hello {name},\n\n" if name else "Hello,\n\n"
    body = state.get("agent_response", "").strip()

    note = ""
    if state.get("requires_approval"):
        if state.get("approval_status") == "approved":
            note = (
                "\n\n(Note: As this is a sensitive request, it was reviewed and "
                "approved by a support supervisor before sending.)"
            )
        elif state.get("approval_status") == "rejected":
            note = (
                "\n\n(Note: This request needs further review; a supervisor will "
                "follow up with you directly.)"
            )
    closing = "\n\nBest regards,\nABC Technologies Support Team"
    return f"{greeting}{body}{note}{closing}"


def supervisor_review(state: SupportState) -> SupportState:
    """LangGraph node: produce the final, validated response."""
    trace = list(state.get("trace", []))

    final = None
    if not llm.is_offline():
        improved = _improve_with_llm(state)
        if improved:
            # Re-apply approval note + signature deterministically around LLM text.
            state["agent_response"] = improved
            final = _improve_offline(state)
    if not final:
        final = _improve_offline(state)

    state["final_response"] = final
    trace.append(
        f"supervisor: validated & finalized response "
        f"(approval={state.get('approval_status')})"
    )
    state["trace"] = trace
    return state
