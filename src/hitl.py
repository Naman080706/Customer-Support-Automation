"""Task 8 — Human-in-the-Loop (HITL) approval process.

High-risk requests (refunds, subscription cancellation, account closure,
compensation, escalation) must be reviewed and approved by a human supervisor
before the final response is sent.

The approval node pauses the automated flow and asks for a supervisor decision.
A pluggable `approval_callback` lets callers supply the decision:
  - interactive console prompt (default in the CLI),
  - auto-approve / auto-reject (used for scripted demos & screenshots).
"""
from __future__ import annotations

from typing import Callable, Optional

from .config import HIGH_RISK_CATEGORIES
from .state import SupportState

# A callback receives the state and returns (decision, approver) where decision
# is "approved" or "rejected".
ApprovalCallback = Callable[[SupportState], tuple[str, str]]

_RISK_LABELS = {
    "refund": "Refund request",
    "subscription_cancellation": "Subscription cancellation",
    "account_closure": "Account closure request",
    "compensation": "Compensation request",
    "escalation": "Escalation to management",
}


def needs_approval(state: SupportState) -> bool:
    return state.get("risk_category", "none") in HIGH_RISK_CATEGORIES


def check_approval_required(state: SupportState) -> SupportState:
    """LangGraph node: flag whether the request needs human approval."""
    trace = list(state.get("trace", []))
    if needs_approval(state):
        state["requires_approval"] = True
        state["approval_status"] = "pending"
        trace.append(
            f"hitl: HIGH-RISK ({_RISK_LABELS.get(state['risk_category'], state['risk_category'])}) "
            f"-> requires human supervisor approval"
        )
    else:
        state["requires_approval"] = False
        state["approval_status"] = "not_required"
        trace.append("hitl: low-risk -> auto-approved (no human needed)")
    state["trace"] = trace
    return state


def _console_approval(state: SupportState) -> tuple[str, str]:
    """Default interactive supervisor prompt."""
    label = _RISK_LABELS.get(state["risk_category"], state["risk_category"])
    print("\n" + "=" * 64)
    print("  HUMAN-IN-THE-LOOP: SUPERVISOR APPROVAL REQUIRED")
    print("=" * 64)
    print(f"  Customer : {state.get('customer_name') or state.get('customer_id')}")
    print(f"  Category : {label}")
    print(f"  Query    : {state['query']}")
    print("  Draft response:")
    print("  " + (state.get("agent_response", "").replace("\n", "\n  ")))
    print("-" * 64)
    answer = input("  Approve this response? [y/N]: ").strip().lower()
    decision = "approved" if answer in ("y", "yes") else "rejected"
    return decision, "supervisor(console)"


def make_auto_callback(decision: str = "approved",
                       approver: str = "supervisor(auto)") -> ApprovalCallback:
    """Return a callback that always returns the given decision (for demos)."""
    def _cb(state: SupportState) -> tuple[str, str]:
        return decision, approver
    return _cb


def human_approval_node(callback: Optional[ApprovalCallback] = None):
    """Factory returning a LangGraph node that performs the approval step."""
    cb = callback or _console_approval

    def _node(state: SupportState) -> SupportState:
        trace = list(state.get("trace", []))
        decision, approver = cb(state)
        state["approval_status"] = decision
        state["approver"] = approver
        if decision == "rejected":
            state["agent_response"] = (
                "Your request requires additional review. A human support "
                "supervisor will personally follow up with you shortly to assist."
            )
        trace.append(f"hitl: supervisor decision = {decision.upper()} by {approver}")
        state["trace"] = trace
        return state

    return _node
