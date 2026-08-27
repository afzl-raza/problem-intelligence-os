from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so Alembic can discover Base.metadata
from app.models.company import Company  # noqa: F401, E402
from app.models.problem import Problem  # noqa: F401, E402
from app.models.company_problem import CompanyProblem  # noqa: F401, E402