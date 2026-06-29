"""Task 7 — SQLite-based conversation memory.

Stores every customer interaction in `memory.db` and retrieves prior
interactions so the system can answer questions like
"What was my previous support issue?" (Query 5).

Schema (table `interactions`):
    id            INTEGER PRIMARY KEY
    customer_id   TEXT     -- stable key per customer
    customer_name TEXT
    query         TEXT
    intent        TEXT
    department    TEXT
    response      TEXT
    created_at    TIMESTAMP
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional

from .config import DB_PATH
from .state import SupportState

SCHEMA = """
CREATE TABLE IF NOT EXISTS interactions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   TEXT NOT NULL,
    customer_name TEXT,
    query         TEXT NOT NULL,
    intent        TEXT,
    department    TEXT,
    response      TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_customer ON interactions(customer_id);
"""


def _connect(db_path=DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH) -> None:
    """Create the database and schema if they do not exist."""
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def save_interaction(state: SupportState, db_path=DB_PATH) -> None:
    """Persist a completed interaction to SQLite."""
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO interactions
               (customer_id, customer_name, query, intent, department, response, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                state.get("customer_id"),
                state.get("customer_name"),
                state.get("query"),
                state.get("intent"),
                state.get("department"),
                state.get("final_response") or state.get("agent_response"),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()


def get_history(customer_id: str, limit: int = 10, db_path=DB_PATH) -> List[sqlite3.Row]:
    """Return prior interactions for a customer, newest first."""
    init_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute(
            """SELECT * FROM interactions
               WHERE customer_id = ?
               ORDER BY id DESC LIMIT ?""",
            (customer_id, limit),
        )
        return cur.fetchall()


def get_known_name(customer_id: str, db_path=DB_PATH) -> Optional[str]:
    for row in get_history(customer_id, limit=50, db_path=db_path):
        if row["customer_name"]:
            return row["customer_name"]
    return None


def load_memory_context(state: SupportState, db_path=DB_PATH) -> SupportState:
    """LangGraph node: attach a summary of prior interactions to the state."""
    rows = get_history(state["customer_id"], limit=5, db_path=db_path)
    trace = list(state.get("trace", []))

    if not state.get("customer_name"):
        known = get_known_name(state["customer_id"], db_path=db_path)
        if known:
            state["customer_name"] = known

    if rows:
        lines = [
            f"- [{r['created_at']}] ({r['department'] or r['intent']}) {r['query']}"
            for r in rows
        ]
        state["memory_context"] = "Recent interactions:\n" + "\n".join(lines)
    else:
        state["memory_context"] = ""
    trace.append(f"memory: loaded {len(rows)} prior interaction(s)")
    state["trace"] = trace
    return state


def memory_recall(state: SupportState, db_path=DB_PATH) -> SupportState:
    """LangGraph node: answer a memory-recall query from stored history.

    Handles Query 5 ("What was my previous support issue?") with no department
    routing -- the answer comes entirely from SQLite memory.
    """
    rows = get_history(state["customer_id"], limit=10, db_path=db_path)
    trace = list(state.get("trace", []))
    name = state.get("customer_name") or get_known_name(state["customer_id"], db_path=db_path)
    greeting = f"Hi {name}, " if name else ""

    # Skip the current memory-recall query itself; find the last real issue.
    previous = None
    for r in rows:
        if not _looks_like_memory_query(r["query"]):
            previous = r
            break

    if previous:
        state["agent_response"] = (
            f"{greeting}your previous support issue was a "
            f"{(previous['department'] or previous['intent'] or 'general')} request: "
            f"\"{previous['query']}\" (logged on {previous['created_at']})."
        )
    else:
        state["agent_response"] = (
            f"{greeting}I don't have any earlier support issues on record for you yet."
        )

    state["department"] = "Memory Recall"
    state["approval_status"] = "not_required"
    state["requires_approval"] = False
    trace.append(f"memory_recall: found {len(rows)} record(s)")
    state["trace"] = trace
    return state


def _looks_like_memory_query(text: str) -> bool:
    t = (text or "").lower()
    return any(s in t for s in ("previous", "last issue", "what was my", "earlier issue", "remember"))
