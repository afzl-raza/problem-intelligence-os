from fastapi import FastAPI
from app.core.config import settings

from app.api.companies import router as companies_router
from app.api.problems import router as problems_router

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

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }