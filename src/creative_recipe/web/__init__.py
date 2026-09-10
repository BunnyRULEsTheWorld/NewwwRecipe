"""Web/API adapter package (thin HTTP layer over the existing NewwwRecipe pipeline).

Modules:
    app                -> FastAPI application factory (`create_app`) and the `app` instance
    models             -> Pydantic transport models mirroring the canonical CIE v3 contract
    service            -> transport <-> domain mapping; calls `creative_recipe.pipeline.run`
    ingredient_catalog -> the 65-item ingredient manifest + scene asset inventory

Nothing here generates recipes or computes CIE scores.

`app` is NOT imported eagerly so that importing e.g. `creative_recipe.web.ingredient_catalog`
does not require FastAPI to be installed.
"""
