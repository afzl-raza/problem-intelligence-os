"""Evaluate keyword vs semantic (vs hybrid) problem search on a manually judged query set.

Reads eval/semantic_queries.json, runs each query against the real database with the
real embedding model, and reports recall@3 / recall@5 / MRR per mode, the similarity
distribution of relevant vs other problems, and a threshold sweep. The thresholds
SEMANTIC_MIN_SIMILARITY / RELATED_MIN_SIMILARITY in app/core/config.py are set from
this output -- not guessed.

Usage (from the backend directory; problems must already be embedded):
    .venv\\Scripts\\python.exe scripts\\eval_semantic.py
"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal, engine  # noqa: E402
from app.models.problem import Problem  # noqa: E402
from app.repositories.embedding import get_embedding_vector, nearest_problems  # noqa: E402
from app.repositories.problem import search_problems as keyword_search  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services.embeddings import embed_query_cached, get_embedder  # noqa: E402
from app.services.hybrid_search import search_problems_hybrid  # noqa: E402

engine.echo = False  # settings.DEBUG would otherwise print every SQL statement

EVAL_FILE = Path(__file__).resolve().parents[1] / "eval" / "semantic_queries.json"


def recall_at(ranked: list[str], relevant: set[str], k: int) -> float:
    return len(set(ranked[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    for position, title in enumerate(ranked, start=1):
        if title in relevant:
            return 1 / position
    return 0.0


def summarize(name: str, rankings: dict[str, list[str]], judged: dict[str, set[str]]) -> None:
    r3 = statistics.mean(recall_at(rankings[q], rel, 3) for q, rel in judged.items())
    r5 = statistics.mean(recall_at(rankings[q], rel, 5) for q, rel in judged.items())
    mrr = statistics.mean(reciprocal_rank(rankings[q], rel) for q, rel in judged.items())
    top1 = statistics.mean(1.0 if rankings[q][:1] and rankings[q][0] in rel else 0.0 for q, rel in judged.items())
    print(f"{name:<22} hit@1 {top1:.2f}   recall@3 {r3:.2f}   recall@5 {r5:.2f}   MRR {mrr:.2f}")


def main() -> None:
    spec = json.loads(EVAL_FILE.read_text(encoding="utf-8"))
    judged = {item["query"]: set(item["relevant"]) for item in spec["queries"]}
    controls = {item["query"] for item in spec["queries"] if item.get("control")}
    negatives = spec["negative_queries"]

    embedder = get_embedder()
    if embedder is None:
        sys.exit("Semantic search is disabled (EMBEDDING_PROVIDER=none).")

    db = SessionLocal()
    try:
        titles = {p.id: p.title for p in db.scalars(select(Problem)).all()}
        known = set(titles.values())
        for query, relevant in judged.items():
            missing = relevant - known
            if missing:
                sys.exit(f"Judged-relevant titles not found in the database for {query!r}: {missing}")

        keyword_rank: dict[str, list[str]] = {}
        semantic_rank: dict[str, list[str]] = {}
        hybrid_rank: dict[str, list[str]] = {}
        similarity: dict[str, dict[str, float]] = {}
        for query in [*judged, *negatives]:
            result = keyword_search(db, query, skip=0, limit=20)
            keyword_rank[query] = [item["problem"].title for item in result["items"]]
            neighbours = nearest_problems(db, embed_query_cached(embedder, query), min_similarity=-1.0, limit=20)
            semantic_rank[query] = [titles[pid] for pid, _ in neighbours]
            hybrid_result = search_problems_hybrid(db, query, limit=20)
            assert hybrid_result["mode_used"] == "hybrid", hybrid_result["semantic_note"]
            hybrid_rank[query] = [item["title"] for item in hybrid_result["items"]]
            similarity[query] = {titles[pid]: sim for pid, sim in neighbours}

        print(f"Model: {embedder.name} | {len(judged)} judged queries, {len(negatives)} negatives, {len(titles)} problems\n")
        summarize("keyword", keyword_rank, judged)
        summarize("semantic (no cutoff)", semantic_rank, judged)
        summarize(f"hybrid (cutoff {settings.SEMANTIC_MIN_SIMILARITY})", hybrid_rank, judged)
        lost = [q for q in judged if not set(keyword_rank[q]) <= set(hybrid_rank[q])]
        print(f"keyword hits missing from hybrid: {len(lost)} of {len(judged)} queries" + (f" {lost}" if lost else ""))
        print(f"negative queries returning anything in hybrid: {sum(1 for q in negatives if hybrid_rank[q])}/{len(negatives)}")
        extra = [len(hybrid_rank[q]) for q in judged]
        print(f"hybrid results per judged query: median {statistics.median(extra)}, max {max(extra)} (of 20 problems)")
        print()

        print("Per query (semantic rank of first relevant | its similarity | keyword found it?):")
        for query, relevant in judged.items():
            rank = next((i for i, t in enumerate(semantic_rank[query], 1) if t in relevant), None)
            best = max((similarity[query][t] for t in relevant), default=0)
            kw = "yes" if set(keyword_rank[query]) & relevant else "NO "
            tag = " [control]" if query in controls else ""
            print(f"  sem#{rank!s:<3} sim {best:.3f}  kw:{kw}  {query}{tag}")
        print()

        relevant_sims = [similarity[q][t] for q, rel in judged.items() for t in rel]
        other_sims = [s for q, rel in judged.items() for t, s in similarity[q].items() if t not in rel]
        negative_top = [max(similarity[q].values()) for q in negatives]
        print(f"Similarity of RELEVANT pairs : min {min(relevant_sims):.3f}  median {statistics.median(relevant_sims):.3f}  max {max(relevant_sims):.3f}")
        print(f"Similarity of OTHER pairs    : min {min(other_sims):.3f}  median {statistics.median(other_sims):.3f}  p95 {sorted(other_sims)[int(len(other_sims) * 0.95)]:.3f}  max {max(other_sims):.3f}")
        print(f"Best match for NEGATIVE queries: {', '.join(f'{s:.3f}' for s in negative_top)}\n")

        print("Threshold sweep (semantic only): precision / recall over judged queries; negatives returning anything")
        print("  thr    precision  recall   neg-queries-with-results")
        for step in range(40, 86, 5):
            t = step / 100
            tp = fp = fn = 0
            for query, relevant in judged.items():
                returned = {title for title, s in similarity[query].items() if s >= t}
                tp += len(returned & relevant)
                fp += len(returned - relevant)
                fn += len(relevant - returned)
            neg = sum(1 for q in negatives if any(s >= t for s in similarity[q].values()))
            precision = tp / (tp + fp) if tp + fp else 1.0
            recall = tp / (tp + fn)
            print(f"  {t:.2f}   {precision:.2f}       {recall:.2f}     {neg}/{len(negatives)}")

        print()
        print("Problem-to-problem neighbours (for calibrating RELATED_MIN_SIMILARITY; judge whether each is a sensible 'related problem'):")
        for pid in titles:
            vector = get_embedding_vector(db, pid)
            neighbours = nearest_problems(db, vector, min_similarity=-1.0, limit=4, exclude_problem_id=pid)
            print(f"  {titles[pid][:62]}")
            for other, sim in neighbours[:3]:
                print(f"      {sim:.3f}  {titles[other][:70]}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
