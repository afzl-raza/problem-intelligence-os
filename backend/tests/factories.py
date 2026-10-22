def make_entry(company_name="Acme Parking", problem_title="Gate queue friction", **overrides):
    """A research-data entry in the scripts/research_data/*.json format."""
    entry = {
        "company_name": company_name,
        "company": {"industry": "Parking", "country": "United States", "funding_stage": "seed"},
        "problem_title": problem_title,
        "problem": {"description": "Drivers queue at exit gates.", "category": "Parking", "impact_level": "medium"},
        "source_name": f"{company_name} -- Official Website",
        "source": {"source_type": "company_website", "base_url": "https://example.com"},
        "source_url": "https://example.com/product",
        "evidence_text": f"{company_name} says it removes exit-gate queues.",
        "relationship_note": "Primary focus per official site.",
    }
    entry.update(overrides)
    return entry
