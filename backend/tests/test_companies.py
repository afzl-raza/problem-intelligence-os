import uuid
from fastapi import status


def test_create_company_success(client):
    payload = {
        "name": "Stripe",
        "legal_name": "Stripe, Inc.",
        "description": "Financial infrastructure for the internet",
        "website_url": "https://stripe.com",
        "linkedin_url": "https://linkedin.com/company/stripe",
        "problem_summary": "Online payment processing complexity for global businesses",
        "industry": "FinTech",
        "country": "United States",
        "city": "San Francisco",
        "founded_year": 2010,
        "funding_stage": "series_c",
        "contact_email": "info@stripe.com",
        "source": "Manual Entry",
    }

    response = client.post("/companies", json=payload)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["name"] == "Stripe"
    assert data["funding_stage"] == "series_c"
    assert "id" in data
    # Verify valid UUID format
    assert uuid.UUID(data["id"])


def test_get_company_by_id_success(client):
    # Create company first
    create_res = client.post(
        "/companies",
        json={"name": "Linear", "industry": "Developer Tools", "funding_stage": "series_a"},
    )
    company_id = create_res.json()["id"]

    response = client.get(f"/companies/{company_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Linear"


def test_get_company_not_found(client):
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/companies/{random_uuid}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Company not found"


def test_get_company_invalid_uuid(client):
    response = client.get("/companies/not-a-valid-uuid")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_company_invalid_funding_stage(client):
    payload = {
        "name": "Invalid Co",
        "funding_stage": "super_mega_seed",  # Invalid enum value
    }
    response = client.post("/companies", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_companies_pagination_envelope(client):
    # Create 3 companies
    for i in range(3):
        client.post("/companies", json={"name": f"Company {i+1}"})

    response = client.get("/companies?skip=0&limit=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert data["total"] == 3
    assert data["skip"] == 0
    assert data["limit"] == 2
    assert len(data["items"]) == 2


def test_list_companies_filtering(client):
    client.post("/companies", json={"name": "Acme AI", "industry": "Artificial Intelligence", "country": "USA", "funding_stage": "seed"})
    client.post("/companies", json={"name": "BioHealth", "industry": "Healthcare", "country": "Germany", "funding_stage": "series_a"})
    client.post("/companies", json={"name": "CyberShield", "industry": "Cybersecurity", "country": "USA", "funding_stage": "seed"})

    # Filter by name substring
    res = client.get("/companies?name=Acme")
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["name"] == "Acme AI"

    # Filter by industry
    res = client.get("/companies?industry=Healthcare")
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["name"] == "BioHealth"

    # Filter by country & funding stage
    res = client.get("/companies?country=USA&funding_stage=seed")
    assert res.status_code == 200
    assert res.json()["total"] == 2


def test_list_companies_invalid_limit(client):
    # Exceed limit cap (>100)
    response = client.get("/companies?limit=150")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Limit below minimum (<1)
    response = client.get("/companies?limit=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_companies_negative_skip(client):
    response = client.get("/companies?skip=-10")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_patch_company_success(client):
    create_res = client.post(
        "/companies",
        json={"name": "Vercel", "funding_stage": "series_a", "city": "San Francisco"},
    )
    company_id = create_res.json()["id"]

    # Partial update
    patch_res = client.patch(
        f"/companies/{company_id}",
        json={"funding_stage": "series_b", "city": "Remote"},
    )
    assert patch_res.status_code == status.HTTP_200_OK
    data = patch_res.json()
    assert data["name"] == "Vercel"  # Unchanged
    assert data["funding_stage"] == "series_b"  # Updated
    assert data["city"] == "Remote"  # Updated


def test_patch_company_not_found(client):
    random_uuid = str(uuid.uuid4())
    response = client.patch(f"/companies/{random_uuid}", json={"name": "New Name"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_company_success(client):
    create_res = client.post("/companies", json={"name": "To Be Deleted"})
    company_id = create_res.json()["id"]

    # Delete
    del_res = client.delete(f"/companies/{company_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify retrieval returns 404
    get_res = client.get(f"/companies/{company_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_delete_company_not_found(client):
    random_uuid = str(uuid.uuid4())
    response = client.delete(f"/companies/{random_uuid}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
