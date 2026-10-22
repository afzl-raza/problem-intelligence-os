from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import DataError

from app.core.config import settings

from app.api.companies import router as companies_router
from app.api.problems import router as problems_router
from app.api.sources import router as sources_router
from app.api.evidence import router as evidence_router
from app.api.ingestion import router as ingestion_router
from app.api.domains import router as domains_router
from app.api.search import router as search_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.exception_handler(DataError)
def handle_database_data_error(request: Request, exc: DataError):
    """A value the database refuses (NUL byte, text longer than its column, ...)
    is the caller's fault, not a server fault. The raw driver message is not
    echoed back."""
    return JSONResponse(
        status_code=422,
        content={"detail": "A submitted value was rejected: it contains characters or exceeds a length the database does not accept."},
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
app.include_router(domains_router)
app.include_router(search_router)

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }

