# AI-Powered Customer Support Automation System (LangGraph)

An automated customer-support system for a SaaS company built with **LangGraph**. It accepts customer queries, classifies the issue, routes it to the right department agent, grounds answers in company documents (RAG), remembers past conversations (SQLite), escalates high-risk requests to a human supervisor, and produces a final validated response.

> **Runs out of the box with no API key.** The system ships with a deterministic,
> rule-based reasoning engine grounded in real RAG retrieval, so it is fully
> reproducible offline. Add a Gemini or OpenAI key (see below) and it will
> automatically use a real LLM instead.

---

## Features → Assignment Tasks

| Task | Feature | Where |
|------|---------|-------|
| 1 | LangGraph workflow | [`src/graph.py`](src/graph.py) |
| 2 | State structure | [`src/state.py`](src/state.py) |
| 3 | Intent classification (Sales/Technical/Billing/Account) | [`src/intent.py`](src/intent.py) |
| 4 | Conditional routing | [`src/router.py`](src/router.py) |
| 5 | Specialized department agents | [`src/agents.py`](src/agents.py) |
| 6 | RAG pipeline over company documents | [`src/rag.py`](src/rag.py) |
| 7 | SQLite conversation memory | [`src/memory.py`](src/memory.py) |
| 8 | Human-in-the-loop approval | [`src/hitl.py`](src/hitl.py) |
| 9 | Supervisor agent (validate & improve) | [`src/supervisor.py`](src/supervisor.py) |
| 10 | Demonstration with 5 sample queries | [`demo.py`](demo.py) |

---

## Project Structure

```
customer-support-automation/
├── README.md                      # this file
├── requirements.txt
├── .env.example                   # optional LLM API keys
├── main.py                        # interactive CLI  (python main.py)
├── demo.py                        # Task 10: runs the 5 sample queries
├── memory.db                      # SQLite memory (created on first run)
├── knowledge_base/                # RAG source documents
│   ├── company_policy.md
│   ├── pricing_guide.md
│   ├── technical_manual.md
│   └── faq.md
├── src/
│   ├── config.py                  # paths, departments, high-risk categories
│   ├── state.py                   # Task 2: SupportState
│   ├── llm.py                     # LLM wrapper + offline fallback
│   ├── intent.py                  # Task 3
│   ├── router.py                  # Task 4
│   ├── agents.py                  # Task 5
│   ├── rag.py                     # Task 6
│   ├── memory.py                  # Task 7
│   ├── hitl.py                    # Task 8
│   ├── supervisor.py              # Task 9
│   └── graph.py                   # Task 1
├── schema.sql                     # SQLite memory schema
└── diagram/
    └── workflow_diagram.png       # LangGraph architecture diagram
```

---

## Setup

Requires **Python 3.10+**.

```bash
# 1. (optional) create a virtual environment
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt
```

### (Optional) Use a real LLM
The system works without any key. To use a real LLM, copy `.env.example` to
`.env` and set one key:

```env
GOOGLE_API_KEY=your_gemini_key      # https://aistudio.google.com/app/apikey
# or
OPENAI_API_KEY=your_openai_key      # https://platform.openai.com/api-keys
```

The provider is auto-detected; classification and agent responses then use the LLM.

---

## How to Run

### Run the demonstration (Task 10 — the 5 sample queries)
```bash
python demo.py
```
This resets `memory.db`, runs all five queries for customer *David*, and prints
the intent, routing, RAG sources, human-in-the-loop trace, memory recall, and
the final response for each.

### Interactive chat
```bash
python main.py
```
Enter a customer id (e.g. `CUST-DAVID`) and type queries. High-risk requests
(refund, cancellation, account closure, compensation, escalation) pause for a
**real supervisor approval** at the console (`y` / `N`).

---

## The 5 Demonstration Queries

| # | Query | Expected path | Result |
|---|-------|---------------|--------|
| 1 | What are the pricing plans available for your software? | Sales | Sales agent + Pricing Guide |
| 2 | I forgot my account password. | Account | Account agent + Technical Manual/FAQ |
| 3 | My application crashes whenever I upload a file. | Technical Support | Technical agent + Technical Manual |
| 4 | I need a refund for my annual subscription. | Billing -> human approval | Billing agent + supervisor approval |
| 5 | What was my previous support issue? | Memory recall (no routing) | Recalls prior issue from SQLite |

---

## How It Works (Pipeline)

```
START → load_memory → classify_intent → route_query ─┬→ sales/technical/billing/account agent → check_approval ─┬→ human_approval ─┐
                                                     │                          (RAG grounds each agent)        └→ (low-risk) ─────┤
                                                     └→ memory_recall ───────────────────────────────────────────────────────────→ supervisor_review → persist → END
```

- **RAG :** each department agent retrieves the top relevant chunks from
  the four knowledge-base documents via a TF-IDF cosine-similarity index (NumPy,
  no external API) and grounds its answer in them.
- **Memory:** every interaction is written to `memory.db`. Memory-recall
  queries are answered directly from stored history.
- **Human-in-the-loop:** the `check_approval` node flags high-risk
  categories; `human_approval` collects the supervisor decision before the
  response is finalized.
- **Supervisor:** validates and improves the draft (adds greeting,
  approval note, professional closing) to produce the final response.
