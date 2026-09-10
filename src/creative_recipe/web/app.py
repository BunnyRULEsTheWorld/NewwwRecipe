"""Minimal FastAPI HTTP adapter in front of the existing NewwwRecipe pipeline.

This module is intentionally THIN. It exposes the existing domain pipeline over HTTP and maps
its canonical CIE v3 result onto transport models. It contains no recipe-generation logic and no
scoring logic of its own.

Endpoints
---------
    GET  /api/health           -> backend/provider/asset status (no secrets)
    GET  /api/ingredients      -> the 65-item ingredient manifest (+ integrity report)
    POST /api/recipes/generate -> run the existing pipeline, return recipe + trace + CIE scores

Static
------
    /ingredients/*  -> repository `ingredient/` directory (read-only)
    /scene/*        -> repository `fronted asset/` directory (read-only)
    /               -> built frontend (`web/dist`) when it exists (optional single-server mode)

Those same URL prefixes are used by the Vite dev server, so asset URLs are identical in
development and in a production build.

Development
-----------
    uvicorn creative_recipe.web.app:app --reload --port 8000

Security: no API key, base URL or model secret is ever returned by any endpoint.
"""
from __future__ import annotations

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import ingredient_catalog as catalog
from .models import (
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    IngredientsResponse,
)
from .service import GenerationUnavailable, generate as run_generation

# Repository root: <root>/src/creative_recipe/web/app.py -> parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
DIST_DIR = Path(os.getenv("NEWWWRECIPE_DIST_DIR", REPO_ROOT / "web" / "dist")).resolve()


def _cors_origins() -> list[str]:
    raw = os.getenv(
        "NEWWWRECIPE_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app() -> FastAPI:
    app = FastAPI(
        title="NewwwRecipe Web API",
        version="1.0.0",
        description=(
            "Thin HTTP adapter over the NewwwRecipe pipeline. Exposes the canonical CIE v3 "
            "contract: a six-stage Innovation Trace and six integer 1-5 weighted dimensions."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    # --- Static assets (read-only; the binaries are never modified) ----------------------
    if catalog.INGREDIENT_DIR.is_dir():
        app.mount(
            catalog.INGREDIENT_URL_PREFIX,
            StaticFiles(directory=str(catalog.INGREDIENT_DIR)),
            name="ingredients",
        )
    if catalog.SCENE_DIR.is_dir():
        app.mount(
            catalog.SCENE_URL_PREFIX,
            StaticFiles(directory=str(catalog.SCENE_DIR)),
            name="scene",
        )

    # --- API ------------------------------------------------------------------------------
    @app.get("/api/health", response_model=HealthResponse, tags=["api"])
    def health() -> HealthResponse:
        from ..config import Config

        cfg = Config.from_env(require_key=False)
        has_key = bool(cfg.hy3_api_key)
        snapshot = catalog.catalog_snapshot()
        return HealthResponse(
            status="ok",
            demo_mode=not has_key,
            provider="demo" if not has_key else "hy3",
            model="demo-offline" if not has_key else cfg.hy3_model,
            ingredient_count=snapshot["count"],
            scene_asset_count=len(catalog.SCENE_ASSETS),
            missing_ingredient_files=snapshot["integrity"]["missingFiles"],
            missing_scene_files=snapshot["integrity"]["missingSceneFiles"],
        )

    @app.get("/api/ingredients", response_model=IngredientsResponse, tags=["api"])
    def ingredients() -> IngredientsResponse:
        snapshot = catalog.catalog_snapshot()
        return IngredientsResponse(**snapshot)

    @app.post("/api/recipes/generate", response_model=GenerateResponse, tags=["api"])
    def recipes_generate(req: GenerateRequest) -> GenerateResponse:
        # Sync `def` -> FastAPI runs it in a threadpool, so the event loop stays responsive.
        try:
            return run_generation(req)
        except GenerationUnavailable as exc:
            # A real configuration/availability problem -> a real error response.
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001 - surfaced verbatim, never masked as success
            raise HTTPException(
                status_code=502,
                detail=(
                    "Recipe generation failed upstream: "
                    f"{type(exc).__name__}: {exc}"
                ),
            ) from exc

    # --- Optional single-server production mode -------------------------------------------
    if DIST_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="frontend")

    return app


app = create_app()
