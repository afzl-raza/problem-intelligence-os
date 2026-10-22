.PHONY: run test migrate revision clean frontend seed

run:
	cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload

test:
	cd backend && .venv\Scripts\python.exe -m pytest tests/test_companies.py -v

migrate:
	cd backend && .venv\Scripts\python.exe -m alembic upgrade head

revision:
	cd backend && .venv\Scripts\python.exe -m alembic revision --autogenerate -m "$(m)"

seed:
	cd backend && .venv\Scripts\python.exe scripts\ingest_research_data.py scripts\research_data\founding_demo.json scripts\research_data\parking_management_saas.json

frontend:
	cd frontend && npm run dev

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
