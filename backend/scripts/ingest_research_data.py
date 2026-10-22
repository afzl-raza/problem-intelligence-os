"""Domain-agnostic research-data ingestion script.

Replaces the old, hardcoded seed_demo_data.py: this script contains no
company/problem data itself. It loads one or more JSON research-data files
(see scripts/research_data/*.json) and ingests them idempotently via
scripts/_ingestion_lib.py.

Each JSON file represents one real-world research pass: a domain
(e.g. "Parking Management SaaS"), when it was researched, and a list of
entries where every company is real and every evidence_text is a faithful
summary of that company's own official page, checked live via WebSearch +
WebFetch at research time -- never recalled from memory and never
fabricated. Every ingested evidence record is structurally forced to
confidence_score=UNVERIFIED and every source to is_verified=False (see
_ingestion_lib.py) since this is illustrative/research-grade data, not
independently verified fact-checking.

To cover a new domain: research it for real (WebSearch + WebFetch against
each company's own site), write a new scripts/research_data/<domain>.json
following the existing files as a template, and run this script against
it. No code changes are needed for a new domain.

Usage (from the backend directory):
    .venv\\Scripts\\python.exe scripts\\ingest_research_data.py research_data\\parking_management_saas.json
    .venv\\Scripts\\python.exe scripts\\ingest_research_data.py research_data\\*.json   (ingest everything)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _ingestion_lib import ingest_entries  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402


def load_dataset(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: ingest_research_data.py <path-to-research-data.json> [more files...]")
        sys.exit(1)

    paths = [Path(arg) for arg in args]
    db = SessionLocal()

    try:
        for path in paths:
            if not path.exists():
                print(f"Skipping {path}: file not found")
                continue

            dataset = load_dataset(path)
            print(f"\n=== {dataset.get('domain', path.stem)} "
                  f"(researched {dataset.get('researched_on', 'unknown date')}) ===")

            results = ingest_entries(db, dataset["entries"])

            totals = {"companies": 0, "problems": 0, "sources": 0, "evidence": 0}
            for result in results:
                totals["companies"] += int(result["company_created"])
                totals["problems"] += int(result["problem_created"])
                totals["sources"] += int(result["source_created"])
                totals["evidence"] += int(result["evidence_created"])

                print(
                    f"- {result['company_name']} <-> {result['problem_title']}: "
                    f"company {'created' if result['company_created'] else 'reused'}, "
                    f"problem {'created' if result['problem_created'] else 'reused'}, "
                    f"source {'created' if result['source_created'] else 'reused'}, "
                    f"evidence {'created' if result['evidence_created'] else 'reused'}"
                )

            print(
                f"Newly created: {totals['companies']} companies, {totals['problems']} problems, "
                f"{totals['sources']} sources, {totals['evidence']} evidence records "
                f"({len(results)} company-problem links verified/upserted)."
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
