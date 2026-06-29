"""Central configuration: paths, departments, and high-risk categories."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # load .env if present (optional API keys)

# --- Paths -----------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
KB_DIR = ROOT_DIR / "knowledge_base"
DB_PATH = ROOT_DIR / "memory.db"

# --- Departments (Section 3 of the assignment) -----------------------------
DEPARTMENTS = {
    "Sales": "Product information, subscription plans, pricing details",
    "Technical": "Application errors, installation issues, login problems, configuration issues",
    "Billing": "Invoice requests, payment issues, refund requests",
    "Account": "Password reset, profile updates, account activation/deactivation",
}

# Map an intent label to the human-readable department name used in responses.
DEPARTMENT_LABELS = {
    "Sales": "Sales",
    "Technical": "Technical Support",
    "Billing": "Billing",
    "Account": "Account",
}

# --- Human-in-the-loop high-risk categories (Section 5) ---------------------
# Any query whose detected risk category is in this set must be approved by a
# human supervisor before the final response is sent.
HIGH_RISK_CATEGORIES = {
    "refund",
    "subscription_cancellation",
    "account_closure",
    "compensation",
    "escalation",
}

# --- LLM mode --------------------------------------------------------------
LLM_MODE = (os.getenv("LLM_MODE") or "").strip().lower()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
