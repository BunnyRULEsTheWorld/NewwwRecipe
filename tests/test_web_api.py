"""Tests for the thin FastAPI web adapter (no real provider, no network).

Run:
    python -m pytest tests/test_web_api.py -q

These tests intentionally exercise the DEMO path (`DemoProvider`) so the whole API can be
verified offline. They also assert the canonical CIE v3 contract: exactly six dimensions,
integer 1-5 scores, and the backend's direct six-dimension weighted total.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from creative_recipe.cie.dimensions import WEIGHTS
from creative_recipe.types import CIEStageDimensions
from creative_recipe.web import ingredient_catalog as catalog
from creative_recipe.web.app import app
from creative_recipe.web import service

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
TS_MANIFEST = REPO_ROOT / "web" / "src" / "data" / "ingredients.ts"

CANONICAL_KEYS = set(CIEStageDimensions.ALL)


@pytest.fixture(autouse=True)
def _no_api_key(monkeypatch):
    """Guarantee demo mode: the real provider must never be contacted from tests."""
    monkeypatch.delenv("HY3_API_KEY", raising=False)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------------------
# health / ingredients
# --------------------------------------------------------------------------------------
def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True
    assert body["ingredient_count"] == 65
    assert body["scene_asset_count"] == 8
    assert body["missing_ingredient_files"] == []
    assert body["missing_scene_files"] == []
    # No secret may leak through the health endpoint.
    assert "api_key" not in resp.text.lower()
    assert "hy3_api_key" not in resp.text.lower()


def test_ingredients_manifest_returns_65_unique(client):
    resp = client.get("/api/ingredients")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 65
    ids = [i["id"] for i in body["ingredients"]]
    files = [i["filename"] for i in body["ingredients"]]
    assert len(set(ids)) == 65
    assert len(set(files)) == 65
    assert body["integrity"]["missingFiles"] == []
    assert body["integrity"]["orphanFiles"] == []


def test_every_referenced_ingredient_file_exists():
    assert catalog.missing_ingredient_files() == []
    assert catalog.orphan_ingredient_files() == []
    assert catalog.missing_scene_files() == []


def test_typescript_manifest_matches_python_catalog():
    """The frontend manifest must not drift from the backend catalog."""
    assert TS_MANIFEST.is_file(), "frontend manifest missing"
    text = TS_MANIFEST.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\['([a-z_]+)',\s*'([^']+)',\s*'([a-z\-]+)'(?:,\s*\[([^\]]*)\])?\]"
    )
    found = pattern.findall(text)
    assert found, "no manifest rows parsed"
    ts_rows = [(fid, name, cat) for (fid, name, cat, _aliases) in found]
    py_rows = [
        (entry["id"], entry["displayName"], entry["category"])
        for entry in catalog.catalog_entries()
    ]
    assert ts_rows == py_rows


# --------------------------------------------------------------------------------------
# request validation
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "payload",
    [
        {"ingredients": ["chicken"]},                       # fewer than two
        {"ingredients": []},                                 # empty
        {"ingredients": ["a", "b"], "unknown": 1},           # extra field forbidden
        {"ingredients": ["a", "b"], "preferences": {"cuisine": "nope"}},
        {"ingredients": ["a"] * 21},                         # too many
    ],
)
def test_request_validation_rejects_bad_payloads(client, payload):
    resp = client.post("/api/recipes/generate", json=payload)
    assert resp.status_code == 422


# --------------------------------------------------------------------------------------
# demo generation
# --------------------------------------------------------------------------------------
def _generate(client, **overrides):
    payload = {
        "ingredients": ["chicken", "coffee"],
        "preferences": {
            "cuisine": "fusion",
            "flavor": "spicy",
            "time": "under-20",
            "constraints": "no nuts please",
        },
    }
    payload.update(overrides)
    return client.post("/api/recipes/generate", json=payload)


def test_demo_generation_succeeds_with_canonical_contract(client):
    resp = _generate(client)
    assert resp.status_code == 200
    body = resp.json()

    # Recipe
    recipe = body["recipe"]
    assert recipe["name"]
    assert recipe["ingredients"]
    assert recipe["seasonings"]
    assert len(recipe["steps"]) >= 1
    assert recipe["creative_explanation"]

    # Meta: demo mode is visible, preferences are echoed back (never dropped).
    meta = body["meta"]
    assert meta["demo_mode"] is True
    assert meta["provider"] == "demo"
    assert meta["requested_preferences"]["flavor"] == "spicy"
    assert meta["requested_preferences"]["time"] == "under-20"
    assert meta["requested_ingredients"] == ["chicken", "coffee"]

    # Innovation Trace: the canonical SIX stages, in order.
    trace = body["trace"]
    assert [s["key"] for s in trace["stages"]] == [
        "existing_culinary_context",
        "ingredient_and_technique_knowledge",
        "innovation_delta",
        "mechanistic_justification",
        "creative_hypothesis",
        "risk_and_constraint",
    ]

    # CIE: six canonical dimensions, exactly once each.
    cie = body["cie"]
    keys = [d["key"] for d in cie["dimensions"]]
    assert len(keys) == 6
    assert set(keys) == CANONICAL_KEYS
    assert len(set(keys)) == 6


def test_cie_scores_are_integers_1_to_5_and_total_is_weighted_sum(client):
    body = _generate(client).json()
    cie = body["cie"]

    expected = 0.0
    for dim in cie["dimensions"]:
        score = dim["score"]
        assert isinstance(score, int)
        assert 1 <= score <= 5
        assert dim["weight"] == pytest.approx(WEIGHTS[dim["key"]])
        assert dim["reason"].strip()
        expected += WEIGHTS[dim["key"]] * score

    # The total is the backend's canonical direct weighted sum, rounded to 4 decimals.
    assert cie["total_score"] == pytest.approx(round(expected, 4))
    assert cie["total_score"] == pytest.approx(4.25)


def test_preferences_reach_the_pipeline_constraints():
    prefs = service.GenerateRequest.model_validate(
        {
            "ingredients": ["chicken", "coffee"],
            "preferences": {
                "cuisine": "chinese",
                "flavor": "savory",
                "time": "under-40",
                "constraints": "no dairy",
            },
            "avoid": ["Old Recipe"],
        }
    )
    text = service.build_constraints(prefs.preferences, prefs.avoid)
    assert "Chinese-inspired" in text
    assert "Savory" in text
    assert "Under 40 minutes" in text
    assert "no dairy" in text
    assert "Old Recipe" in text


def test_real_provider_without_key_is_an_error_not_a_silent_fallback(monkeypatch):
    monkeypatch.delenv("HY3_API_KEY", raising=False)
    with pytest.raises(service.GenerationUnavailable):
        service.resolve_provider(force_demo=False)


def test_backend_failure_returns_a_real_error_response(client, monkeypatch):
    """A pipeline failure must surface as a real error — never an invented recipe."""

    def boom(*args, **kwargs):
        raise RuntimeError("upstream exploded")

    monkeypatch.setattr(service, "run_pipeline", boom)
    resp = _generate(client)
    assert resp.status_code == 502
    assert "upstream exploded" in resp.json()["detail"]


def test_unavailable_generation_returns_503(client, monkeypatch):
    def nope(*args, **kwargs):
        raise service.GenerationUnavailable("no key configured")

    monkeypatch.setattr(service, "run_pipeline", nope)
    resp = _generate(client)
    assert resp.status_code == 503
    assert "no key configured" in resp.json()["detail"]
