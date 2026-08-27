from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine,
)
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()