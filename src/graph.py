"""Task 1 — LangGraph workflow assembly.

Wires every node into a single StateGraph:

    START
      -> load_memory            (Task 7: pull prior history from SQLite)
      -> classify_intent        (Task 3: Sales/Technical/Billing/Account/Memory)
      -> route_query  ──────────(Task 4: conditional routing)
           ├── memory_recall    (answer from memory, no department)
           ├── sales_agent      ┐
           ├── technical_agent  │ (Task 5 specialized agents,
           ├── billing_agent    │  each grounded by RAG — Task 6)
           └── account_agent    ┘
                 -> check_approval        (Task 8: is it high-risk?)
                       ├── human_approval (Task 8: supervisor decision)
                       └── (low-risk: skip)
      -> supervisor_review      (Task 9: validate & improve -> final response)
      -> persist                (Task 7: save interaction to SQLite)
      -> END
"""
from __future__ import annotations

from typing import Optional

from langgraph.graph import END, START, StateGraph

from . import memory as mem
from .agents import account_agent, billing_agent, sales_agent, technical_agent
from .hitl import ApprovalCallback, check_approval_required, human_approval_node
from .intent import classify_intent
from .memory import load_memory_context, memory_recall
from .router import route_query
from .state import SupportState
from .supervisor import supervisor_review


def _persist_node(state: SupportState) -> SupportState:
    """Final node: store the completed interaction in SQLite memory."""
    mem.save_interaction(state)
    trace = list(state.get("trace", []))
    trace.append("persist: interaction saved to memory.db")
    state["trace"] = trace
    return state


def _approval_branch(state: SupportState) -> str:
    """Conditional edge after the department agent."""
    return "human_approval" if state.get("requires_approval") else "supervisor_review"


def build_graph(approval_callback: Optional[ApprovalCallback] = None):
    """Construct and compile the customer-support LangGraph workflow."""
    graph = StateGraph(SupportState)

    # --- Nodes ---
    graph.add_node("load_memory", load_memory_context)
    graph.add_node("classify_intent", classify_intent)

    graph.add_node("sales_agent", sales_agent)
    graph.add_node("technical_agent", technical_agent)
    graph.add_node("billing_agent", billing_agent)
    graph.add_node("account_agent", account_agent)
    graph.add_node("memory_recall", memory_recall)

    graph.add_node("check_approval", check_approval_required)
    graph.add_node("human_approval", human_approval_node(approval_callback))
    graph.add_node("supervisor_review", supervisor_review)
    graph.add_node("persist", _persist_node)

    # --- Entry: load memory, then classify ---
    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "classify_intent")

    # --- Task 4: conditional routing on intent ---
    graph.add_conditional_edges(
        "classify_intent",
        route_query,
        {
            "sales_agent": "sales_agent",
            "technical_agent": "technical_agent",
            "billing_agent": "billing_agent",
            "account_agent": "account_agent",
            "memory_recall": "memory_recall",
        },
    )

    # --- Department agents -> approval check ---
    for node in ("sales_agent", "technical_agent", "billing_agent", "account_agent"):
        graph.add_edge(node, "check_approval")

    # --- Task 8: approval branch ---
    graph.add_conditional_edges(
        "check_approval",
        _approval_branch,
        {"human_approval": "human_approval", "supervisor_review": "supervisor_review"},
    )
    graph.add_edge("human_approval", "supervisor_review")

    # --- Memory recall skips departments & approval, goes straight to supervisor ---
    graph.add_edge("memory_recall", "supervisor_review")

    # --- Task 9 -> persist -> END ---
    graph.add_edge("supervisor_review", "persist")
    graph.add_edge("persist", END)

    return graph.compile()


def handle_query(app, customer_id: str, query: str) -> SupportState:
    """Run a single query through the compiled graph and return final state."""
    from .state import new_state
    init = new_state(customer_id, query)
    result = app.invoke(init)
    return result
