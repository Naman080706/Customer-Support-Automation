"""Build the clean submission folder + ZIP (checklist items only)."""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
SUBMISSION = BUILD / "submission"

# The genuine project files that go inside source_code.zip (core app only).
SOURCE_INCLUDE = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    ".env.example",
    "schema.sql",
    "main.py",
    "demo.py",
    "src/__init__.py",
    "src/config.py",
    "src/state.py",
    "src/llm.py",
    "src/intent.py",
    "src/router.py",
    "src/agents.py",
    "src/rag.py",
    "src/memory.py",
    "src/hitl.py",
    "src/supervisor.py",
    "src/graph.py",
    "knowledge_base/company_policy.md",
    "knowledge_base/pricing_guide.md",
    "knowledge_base/technical_manual.md",
    "knowledge_base/faq.md",
    "diagram/workflow_diagram.png",
]


def build_source_zip(dest: Path) -> Path:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in SOURCE_INCLUDE:
            zf.write(ROOT / rel, rel)
    return dest


def main():
    if SUBMISSION.exists():
        shutil.rmtree(SUBMISSION)
    SUBMISSION.mkdir(parents=True)

    # 1. Source Code (.zip)
    build_source_zip(SUBMISSION / "source_code.zip")
    # 2-6. checklist deliverables
    shutil.copy2(ROOT / "README.md", SUBMISSION / "README.md")
    shutil.copy2(ROOT / "diagram" / "workflow_diagram.png", SUBMISSION / "workflow_diagram.png")
    shutil.copy2(ROOT / "docs" / "screenshots.pdf", SUBMISSION / "screenshots.pdf")
    shutil.copy2(ROOT / "memory.db", SUBMISSION / "memory.db")
    shutil.copy2(ROOT / "schema.sql", SUBMISSION / "schema.sql")

    # Single submission ZIP with the checklist items at the top level.
    final = BUILD / "Assignment2_Customer_Support_Automation.zip"
    with zipfile.ZipFile(final, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(SUBMISSION.iterdir()):
            zf.write(p, p.name)

    print("Submission folder:", SUBMISSION)
    for p in sorted(SUBMISSION.iterdir()):
        print(f"   - {p.name:24} {p.stat().st_size // 1024 or 1:>4} KB")
    print("\nSubmission ZIP   :", final, f"({final.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
