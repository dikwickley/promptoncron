from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.results import router as results_router
from app.api.runs import router as runs_router
from app.api.tasks import router as tasks_router
from app.models import Base  # noqa: F401 (import side effects for metadata)
from app.database import ENGINE


def create_app() -> FastAPI:
    app = FastAPI(title="promptoncron", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    app.include_router(tasks_router)
    app.include_router(runs_router)
    app.include_router(results_router)
    return app


app = create_app()


@app.on_event("startup")
def _startup() -> None:
    # MVP convenience: auto-create tables.
    Base.metadata.create_all(bind=ENGINE)


