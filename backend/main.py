from typing import Dict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import settings
from backend.database.db import init_db
from backend.api.routes.documents import router as documents_router

from backend.utils.logger import setup_logger

from backend.api.routes.search import router as search_router
from backend.services.index_builder import build_index
from backend.api.routes.chat import (
    router as chat_router
)


logger = setup_logger("main")

# Initialize FastAPI App
app = FastAPI(
    title="AI Research Assistant - Backend Module",
    description="Backend API infrastructure and document ingestion pipeline.",
    version="1.0.0"
)

# 1. CORS Middleware configuration allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Startup event to initialize SQLite DB
@app.on_event("startup")
async def startup_event() -> None:

    logger.info(
        "Application starting up. Initializing database..."
    )

    try:

        await init_db()

        logger.info(
            "Database schema initialized successfully."
        )

        await build_index()

        logger.info(
            "Retrieval indexes built successfully (FAISS + BM25)."
        )

    except Exception as e:

        logger.error(
            f"Startup failed: {str(e)}"
        )

        raise e
# 3. Mount routers under /api/v1
# This mounts documents_router (which has prefix /documents) under /api/v1
# Making the endpoints accessible at /api/v1/documents/...
app.include_router(documents_router, prefix="/api/v1")

# 4. Global Exception Handlers returning JSON errors
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Format HTTP exceptions into clean JSON response."""
    logger.warning(f"HTTP error on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPException", "detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Format Pydantic schema validation exceptions."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"error": "ValidationError", "detail": str(exc.errors())}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for internal server errors to prevent traceback leaks."""
    logger.exception(f"Unhandled exception on {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": f"An unexpected error occurred: {str(exc)}"
        }
    )

# 5. Root level health check GET /health -> {"status": "ok"}
'''
@app.get("/health", tags=["health"])
async def root_health() -> Dict[str, str]:
    """Root-level health check endpoint."""
    return {"status": "ok"}   
'''
@app.get("/health")
async def root():
    return {
        "message": "AI Research Assistant Backend Running",
        "docs": "/docs",
        "health": "/health",
        "status": "ok"
    }

# GET /api/v1/health fallback returning version
@app.get("/api/v1/health", tags=["health"])
async def api_health() -> Dict[str, str]:
    """API-level health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}

app.include_router(
    search_router,
    prefix="/api/v1"
)

app.include_router(
    chat_router,
    prefix="/api/v1"
)
