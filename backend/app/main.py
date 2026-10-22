from fastapi import FastAPI
from app.core.config import settings

from app.api.companies import router as companies_router
from app.api.problems import router as problems_router
from app.api.sources import router as sources_router
from app.api.evidence import router as evidence_router
from app.api.ingestion import router as ingestion_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "message": "Welcome to Problem Intelligence OS API",
    }

app.include_router(companies_router)
app.include_router(problems_router)
app.include_router(sources_router)
app.include_router(evidence_router)
app.include_router(ingestion_router)

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }
