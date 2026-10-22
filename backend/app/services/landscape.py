from sqlalchemy.orm import Session

from app.models.problem import ImpactLevel
from app.repositories.landscape import get_domain_landscape as get_domain_landscape_repo
from app.services.domain import to_response_dict
from app.services.evidence import is_verified_evidence


def get_domain_landscape(
    db: Session,
    slug: str,
    category: str | None = None,
    impact_level: ImpactLevel | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict | None:
    data = get_domain_landscape_repo(
        db, slug, category=category, impact_level=impact_level, skip=skip, limit=limit
    )
    if data is None:
        return None

    return {
        "domain": to_response_dict(*data["domain"]),
        "categories": [{"category": name, "problem_count": count} for name, count in data["categories"]],
        "impact_distribution": [{"impact_level": level, "problem_count": count} for level, count in data["impacts"]],
        "funding_distribution": [{"funding_stage": stage, "company_count": count} for stage, count in data["funding"]],
        "companies": [
            {
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
                "website_url": company.website_url,
                "funding_stage": company.funding_stage,
                "problem_count": problem_count,
            }
            for company, problem_count in data["companies"]
        ],
        "problems": [
            {
                "id": item["problem"].id,
                "title": item["problem"].title,
                "description": item["problem"].description,
                "category": item["problem"].category,
                "impact_level": item["problem"].impact_level,
                "company_count": item["company_count"],
                "evidence_count": len(item["evidence"]),
                "verified_evidence_count": sum(
                    is_verified_evidence(confidence, source_verified) for confidence, source_verified in item["evidence"]
                ),
            }
            for item in data["problems"]
        ],
        "problems_total": data["problems_total"],
        "skip": skip,
        "limit": limit,
    }
