.PHONY: run test migrate revision clean

run:
	cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload

test:
	cd backend && .venv\Scripts\python.exe -m pytest tests/test_companies.py -v

migrate:
	cd backend && .venv\Scripts\python.exe -m alembic upgrade head

revision:
	cd backend && .venv\Scripts\python.exe -m alembic revision --autogenerate -m "$(m)"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
