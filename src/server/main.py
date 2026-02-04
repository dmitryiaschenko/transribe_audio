"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.config import CORS_ORIGINS, BASE_DIR
from src.server.routes import router
from src.server.jobs import job_manager
from src.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Transcription API server")
    yield
    # Cleanup on shutdown
    logger.info("Shutting down Transcription API server")
    job_manager.cleanup_old_jobs(max_age_hours=0)


app = FastAPI(
    title="Transcription API",
    description="Audio transcription service using Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount static files for production (React build)
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
    logger.info(f"Serving static files from {frontend_dist}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Run the server with uvicorn."""
    import uvicorn
    uvicorn.run(
        "src.server.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run_server(reload=True)
