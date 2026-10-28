"""Builds the FastAPI app: API routes, plus the built React frontend if present."""

from collections.abc import Callable
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import __version__, config, db, security
from .budget.api import router as budget_router

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def create_app(
    db_path: Path | str | None = None,
    clock: Callable[[], date] = date.today,
    settings: config.Settings | None = None,
) -> FastAPI:
    settings = settings or config.load_settings()
    app = FastAPI(title="TurtleMaxxxing", version=__version__, docs_url="/api/docs", redoc_url=None)
    app.state.db_path = db_path or config.db_path()
    app.state.clock = clock
    app.state.last_tick = None
    app.state.settings = settings

    conn = db.connect(app.state.db_path)
    try:
        db.migrate(conn)
    finally:
        conn.close()

    security.install(app, settings.allowed_hosts)

    @app.get("/api/health")
    def health():
        return {"ok": True, "version": __version__, "today": clock().isoformat(), "url": settings.url}

    app.include_router(budget_router)

    if FRONTEND_DIST.is_dir():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    return app
