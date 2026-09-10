"""Canonical ingredient catalog for the web adapter.

The catalog is the single authoritative list of the 65 ingredient illustrations shipped in the
repository's ``ingredient/`` directory. It is intentionally a *plain data* module (no I/O at import
time) so it can be used by tests, by the API layer and by the asset-integrity check without
touching the filesystem.

Each entry mirrors the frontend TypeScript manifest ``web/src/data/ingredients.ts``:
``id``, ``displayName``, ``filename``, ``category`` and optional ``aliases``. A dedicated test
(``tests/test_web_api.py``) asserts that the two manifests never drift apart.

The illustration binaries themselves are NOT modified, renamed or recompressed here.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Repository root: <root>/src/creative_recipe/web/ingredient_catalog.py -> parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]

#: Directory holding the 65 transparent ingredient PNGs (overridable for tests / deployments).
INGREDIENT_DIR = Path(
    os.getenv("NEWWWRECIPE_INGREDIENT_DIR", REPO_ROOT / "ingredient")
).resolve()

#: Directory holding the eight scene illustrations (note the historical spelling of the folder).
SCENE_DIR = Path(
    os.getenv("NEWWWRECIPE_SCENE_DIR", REPO_ROOT / "fronted asset")
).resolve()

#: Public URL prefixes used by both the FastAPI static mounts and the Vite dev server.
INGREDIENT_URL_PREFIX = "/ingredients"
SCENE_URL_PREFIX = "/scene"


# --- Categories -----------------------------------------------------------------
# Key -> (display label)
CATEGORIES: Dict[str, str] = {
    "vegetables": "Vegetables",
    "fruits": "Fruits",
    "protein": "Protein",
    "dairy-eggs": "Dairy & Eggs",
    "grains": "Grains & Staples",
    "pantry": "Pantry & Flavor",
}

#: Stable display order of the category tabs.
CATEGORY_ORDER: Tuple[str, ...] = (
    "vegetables",
    "fruits",
    "protein",
    "dairy-eggs",
    "grains",
    "pantry",
)


# --- The 65 canonical ingredients -----------------------------------------------
# (id, displayName, filename, category, aliases)
_CATALOG: Tuple[Tuple[str, str, str, str, Tuple[str, ...]], ...] = (
    # Vegetables
    ("bell_pepper", "Bell Pepper", "bell_pepper.png", "vegetables", ("capsicum", "sweet pepper")),
    ("bok_choy", "Bok Choy", "bok_choy.png", "vegetables", ("pak choi", "chinese cabbage green")),
    ("broccoli", "Broccoli", "broccoli.png", "vegetables", ()),
    ("cabbage", "Cabbage", "cabbage.png", "vegetables", ()),
    ("carrot", "Carrot", "carrot.png", "vegetables", ()),
    ("cauliflower", "Cauliflower", "cauliflower.png", "vegetables", ()),
    ("celery", "Celery", "celery.png", "vegetables", ()),
    ("corn", "Corn", "corn.png", "vegetables", ("sweetcorn", "maize")),
    ("cucumber", "Cucumber", "cucumber.png", "vegetables", ()),
    ("daikon_radish", "Daikon Radish", "daikon_radish.png", "vegetables", ("daikon", "white radish")),
    ("eggplant", "Eggplant", "eggplant.png", "vegetables", ("aubergine",)),
    ("garlic", "Garlic", "garlic.png", "vegetables", ()),
    ("ginger", "Ginger", "ginger.png", "vegetables", ()),
    ("green_beans", "Green Beans", "green_beans.png", "vegetables", ("string beans",)),
    ("lettuce", "Lettuce", "lettuce.png", "vegetables", ()),
    ("lotus_root", "Lotus Root", "lotus_root.png", "vegetables", ("renkon",)),
    ("mushroom", "Mushroom", "mushroom.png", "vegetables", ()),
    ("napa_cabbage", "Napa Cabbage", "napa_cabbage.png", "vegetables", ("chinese cabbage",)),
    ("onion", "Onion", "onion.png", "vegetables", ()),
    ("potato", "Potato", "potato.png", "vegetables", ()),
    ("pumpkin", "Pumpkin", "pumpkin.png", "vegetables", ("squash",)),
    ("scallion", "Scallion", "scallion.png", "vegetables", ("green onion", "spring onion")),
    ("spinach", "Spinach", "spinach.png", "vegetables", ()),
    ("sweet_potato", "Sweet Potato", "sweet_potato.png", "vegetables", ("yam",)),
    ("tomato", "Tomato", "tomato.png", "vegetables", ()),
    ("zucchini", "Zucchini", "zucchini.png", "vegetables", ("courgette",)),
    # Fruits
    ("apple", "Apple", "apple.png", "fruits", ()),
    ("avocado", "Avocado", "avocado.png", "fruits", ()),
    ("banana", "Banana", "banana.png", "fruits", ()),
    ("lemon", "Lemon", "lemon.png", "fruits", ()),
    ("orange", "Orange", "orange.png", "fruits", ()),
    ("pear", "Pear", "pear.png", "fruits", ()),
    ("strawberry", "Strawberry", "strawberry.png", "fruits", ()),
    # Protein
    ("bacon", "Bacon", "bacon.png", "protein", ()),
    ("beef", "Beef", "beef.png", "protein", ()),
    ("chicken", "Chicken", "chicken.png", "protein", ()),
    ("chickpeas", "Chickpeas", "chickpeas.png", "protein", ("garbanzo",)),
    ("pork", "Pork", "pork.png", "protein", ()),
    ("salmon", "Salmon", "salmon.png", "protein", ()),
    ("shrimp", "Shrimp", "shrimp.png", "protein", ("prawn",)),
    ("squid", "Squid", "squid.png", "protein", ("calamari",)),
    ("tofu", "Tofu", "tofu.png", "protein", ("bean curd",)),
    ("white_fish", "White Fish", "white_fish.png", "protein", ("cod", "tilapia")),
    # Dairy & Eggs
    ("butter", "Butter", "butter.png", "dairy-eggs", ()),
    ("cheese", "Cheese", "cheese.png", "dairy-eggs", ()),
    ("cream", "Cream", "cream.png", "dairy-eggs", ()),
    ("egg", "Egg", "egg.png", "dairy-eggs", ("eggs",)),
    ("milk", "Milk", "milk.png", "dairy-eggs", ()),
    ("yogurt", "Yogurt", "yogurt.png", "dairy-eggs", ("yoghurt",)),
    # Grains & Staples
    ("bread", "Bread", "bread.png", "grains", ()),
    ("flour", "Flour", "flour.png", "grains", ()),
    ("noodles", "Noodles", "noodles.png", "grains", ()),
    ("oats", "Oats", "oats.png", "grains", ()),
    ("pasta", "Pasta", "pasta.png", "grains", ()),
    ("rice", "Rice", "rice.png", "grains", ()),
    ("tortilla", "Tortilla", "tortilla.png", "grains", ("wrap",)),
    # Pantry & Flavor
    ("chili_pepper", "Chili Pepper", "chili_pepper.png", "pantry", ("chilli", "hot pepper")),
    ("cilantro", "Cilantro", "cilantro.png", "pantry", ("coriander leaf",)),
    ("coffee", "Coffee", "coffee.png", "pantry", ("espresso",)),
    ("curry_paste", "Curry Paste", "curry_paste.png", "pantry", ()),
    ("dark_chocolate", "Dark Chocolate", "dark_chocolate.png", "pantry", ("chocolate",)),
    ("honey", "Honey", "honey.png", "pantry", ()),
    ("kimchi", "Kimchi", "kimchi.png", "pantry", ()),
    ("miso", "Miso", "miso.png", "pantry", ()),
    ("soy_sauce", "Soy Sauce", "soy_sauce.png", "pantry", ("shoyu",)),
)

#: Number of ingredients the catalog is contractually expected to expose.
EXPECTED_INGREDIENT_COUNT = 65


def catalog_entries() -> List[dict]:
    """Return the catalog as a list of plain dicts (JSON-serialisable)."""
    return [
        {
            "id": _id,
            "displayName": display,
            "filename": filename,
            "category": category,
            "aliases": list(aliases),
            "url": f"{INGREDIENT_URL_PREFIX}/{filename}",
        }
        for (_id, display, filename, category, aliases) in _CATALOG
    ]


def catalog_ids() -> List[str]:
    return [_id for (_id, _display, _f, _c, _a) in _CATALOG]


def display_name(ingredient_id: str) -> str:
    """Human display name for a catalog id; falls back to a title-cased id."""
    for (_id, display, _f, _c, _a) in _CATALOG:
        if _id == ingredient_id:
            return display
    return ingredient_id.replace("_", " ").title()


def ingredient_path(filename: str) -> Path:
    """Absolute path of an ingredient PNG. Never writes; only resolves."""
    return INGREDIENT_DIR / filename


def missing_ingredient_files() -> List[str]:
    """Filenames declared by the catalog that do not exist on disk."""
    return [f for (_i, _d, f, _c, _a) in _CATALOG if not (INGREDIENT_DIR / f).is_file()]


def orphan_ingredient_files() -> List[str]:
    """PNG files present on disk that the catalog does not declare."""
    declared = {f for (_i, _d, f, _c, _a) in _CATALOG}
    if not INGREDIENT_DIR.is_dir():
        return []
    return sorted(
        p.name
        for p in INGREDIENT_DIR.glob("*.png")
        if p.name not in declared
    )


#: The eight scene illustrations required by the frontend.
SCENE_ASSETS: Tuple[str, ...] = (
    "kitchen_background_wide.png",
    "fridge_closed.png",
    "fridge_ajar.png",
    "fridge_open_empty.png",
    "basket_empty.png",
    "magic_mixing_bowl.png",
    "recipe_book_open_blank.png",
    "favorites_recipe_box_empty.png",
)


def scene_url(filename: str) -> str:
    return f"{SCENE_URL_PREFIX}/{filename}"


def missing_scene_files() -> List[str]:
    return [f for f in SCENE_ASSETS if not (SCENE_DIR / f).is_file()]


def catalog_snapshot() -> dict:
    """Everything /api/ingredients needs, plus integrity information."""
    entries = catalog_entries()
    return {
        "count": len(entries),
        "categories": [{"id": k, "label": CATEGORIES[k]} for k in CATEGORY_ORDER],
        "ingredients": entries,
        "integrity": {
            "expectedCount": EXPECTED_INGREDIENT_COUNT,
            "missingFiles": missing_ingredient_files(),
            "orphanFiles": orphan_ingredient_files(),
            "missingSceneFiles": missing_scene_files(),
        },
    }


def resolve_ingredient_dir() -> Optional[Path]:
    return INGREDIENT_DIR if INGREDIENT_DIR.is_dir() else None
