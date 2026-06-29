"""Capture the program's console execution into screenshots.pdf.

Runs the demonstration, captures the real terminal output, then queries the
SQLite database, and renders both as plain terminal-style screenshots.

Output:  docs/screenshots.pdf
Run:     python tools/generate_screenshots_pdf.py
"""
from __future__ import annotations

import io
import sqlite3
import sys
from contextlib import redirect_stdout
from pathlib import Path

import matplotlib
from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import DB_PATH  # noqa: E402
from demo import run_demo  # noqa: E402

DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

# DejaVu Sans Mono ships with matplotlib -> Unicode + monospace in fpdf2.
MONO = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSansMono.ttf"

# Plain terminal look.
BG = (12, 12, 12)
FG = (208, 208, 208)
PROMPT = (235, 235, 235)

PROMPT_PREFIX = "PS C:\\Users\\Naman\\Desktop\\customer-support-automation>"


def _capture_console() -> str:
    """Build a realistic terminal session: run the demo, then query the DB."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_demo(fresh=True)
    demo_out = buf.getvalue()

    # Query the memory database the way one would from the shell.
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, customer_id, intent, department, query FROM interactions ORDER BY id"
    ).fetchall()
    conn.close()
    db_lines = ["id|customer_id|intent|department|query"]
    for r in rows:
        q = (r["query"] or "")
        db_lines.append(f"{r['id']}|{r['customer_id']}|{r['intent']}|{r['department']}|{q}")
    db_out = "\n".join(db_lines)

    session = (
        f"{PROMPT_PREFIX} python demo.py\n"
        f"{demo_out}\n"
        f"{PROMPT_PREFIX} sqlite3 memory.db \"SELECT id, customer_id, intent, department, query FROM interactions;\"\n"
        f"{db_out}\n"
        f"{PROMPT_PREFIX}"
    )
    return session


def _render(text: str) -> Path:
    lines = text.replace("\t", "    ").splitlines()
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_font("mono", "", str(MONO))

    left, top, bottom = 8, 10, 288
    line_h = 4.0
    wrap = 108

    def new_page():
        pdf.add_page()
        pdf.set_fill_color(*BG)
        pdf.rect(0, 0, 210, 297, "F")
        pdf.set_font("mono", "", 7.4)

    new_page()
    y = top
    for raw in lines:
        segs = [raw[i:i + wrap] for i in range(0, max(len(raw), 1), wrap)] or [""]
        for seg in segs:
            if y > bottom:
                new_page()
                y = top
            pdf.set_text_color(*(PROMPT if seg.startswith("PS C:") else FG))
            pdf.set_xy(left, y)
            pdf.cell(0, line_h, seg)
            y += line_h

    out = DOCS / "screenshots.pdf"
    pdf.output(str(out))
    return out


def main():
    text = _capture_console()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(text)
    out = _render(text)
    print(f"\n[pdf] wrote {out}")


if __name__ == "__main__":
    main()
