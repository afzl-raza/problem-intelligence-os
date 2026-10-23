"""CLI loader for researched datasets in scripts/research_data/*.json.

Contains no company/problem data itself; all ingestion rules live in
app/services/research_ingestion.py. Each JSON file is one real research
pass: every company is real and every evidence_text faithfully summarizes
that company's own official page, checked live (WebSearch + WebFetch) at
research time. To cover a new domain, research it and add a JSON file —
no code changes needed.

Dataset format:
    {
      "dataset": "<label>",
      "researched_on": "YYYY-MM-DD",
      "default_domains": ["<Domain name>", ...],   # optional
      "entries": [ { ..., "domains": [...] }, ... ] # per-entry override optional
    }

Add --embed to also embed any new or changed problems for semantic search afterwards.

Usage (from the backend directory):
    .venv\\Scripts\\python.exe scripts\\ingest_research_data.py scripts\\research_data\\parking_management_saas.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import SessionLocal  # noqa: E402
from app.services.research_ingestion import ingest_dataset  # noqa: E402


def _created(flag: bool) -> str:
    return "created" if flag else "reused"


def main() -> None:
    args = sys.argv[1:]
    embed = "--embed" in args
    paths = [Path(arg) for arg in args if not arg.startswith("--")]
    if not paths:
        print("Usage: ingest_research_data.py <dataset.json> [more.json ...]")
        sys.exit(1)

    db = SessionLocal()
    try:
        for path in paths:
            if not path.exists():
                print(f"Skipping {path}: file not found")
                continue

            with path.open(encoding="utf-8") as f:
                dataset = json.load(f)

            print(f"\n=== {dataset.get('dataset', path.stem)} (researched {dataset.get('researched_on', 'unknown')}) ===")
            results = ingest_dataset(db, dataset)

            for r in results:
                print(
                    f"- {r['company_name']} <-> {r['problem_title']} [{', '.join(r['domains']) or 'no domain'}]: "
                    f"company {_created(r['company_created'])}, problem {_created(r['problem_created'])}, "
                    f"source {_created(r['source_created'])}, evidence {_created(r['evidence_created'])}"
                )

            print(
                "Newly created: "
                f"{sum(r['company_created'] for r in results)} companies, "
                f"{sum(r['problem_created'] for r in results)} problems, "
                f"{sum(r['source_created'] for r in results)} sources, "
                f"{sum(r['evidence_created'] for r in results)} evidence records, "
                f"{sum(r['domains_created'] for r in results)} domains."
            )
    finally:
        db.close()

    if embed:
        from embed_problems import run as embed_problems

        embed_problems()


if __name__ == "__main__":
    main()
