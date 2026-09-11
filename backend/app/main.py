import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.api.settings_routes import router as settings_router
from app.api.generation_routes import router as generation_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

settings = get_settings()

# The built frontend, when it exists. Serving it from here means one public
# URL and one origin: no CORS, and no API base URL to configure.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered video editing for social media",
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes. Settings and generation come first because they have no heavy
# dependencies; the editor router pulls in moviepy/librosa, which are large and
# can fail to install on a small host. If that happens the Studio and the
# Integrações screen still work, and the log says what is missing.
app.include_router(settings_router)
app.include_router(generation_router)

try:
    from app.api.routes import router as editor_router

    app.include_router(editor_router)
    EDITOR_AVAILABLE = True
except Exception as exc:  # noqa: BLE001 - a missing media dep must not kill the app
    EDITOR_AVAILABLE = False
    logger.warning(
        "Editor routes unavailable (%s). Generation and settings still work; "
        "install the video dependencies to enable video editing.",
        exc,
    )


@app.get("/api")
async def api_root():
    """Service description, kept off / so the SPA can own the root path."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "editor_available": EDITOR_AVAILABLE,
        "frontend_bundled": FRONTEND_DIST.is_dir(),
        "docs": "/docs",
    }


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    if FRONTEND_DIST.is_dir():
        logger.info("Serving the built frontend from %s", FRONTEND_DIST)
    else:
        logger.info("No frontend build found; serving the API only.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")


# --- Single-page app -------------------------------------------------------
# Registered last so every API route above wins the match.
if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    RESERVED_PREFIXES = ("api", "docs", "redoc", "openapi.json")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """
        Serve the built page, falling back to index.html so client-side routes
        like /gerar survive a refresh or a link opened directly.
        """
        if full_path.split("/", 1)[0] in RESERVED_PREFIXES:
            raise HTTPException(status_code=404, detail="Not found")

        if full_path:
            candidate = (FRONTEND_DIST / full_path).resolve()
            # Never serve outside the build directory.
            if candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST.resolve()):
                return FileResponse(candidate)

        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
