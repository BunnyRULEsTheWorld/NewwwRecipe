"""Audit the supplied illustration assets (read-only, never modifies a binary).

Checks
------
1. `ingredient/` contains exactly the 65 expected snake_case PNG stems (missing / duplicate /
   orphan report).
2. Every PNG decodes (PIL `verify()` + `load()`), with dimensions and mode.
3. Every ingredient cutout actually has an alpha channel and a meaningful transparent region.
4. `milk.png` visibly contains opaque milk (opaque-pixel ratio + mean colour of opaque pixels).
5. The eight scene illustrations in `fronted asset/` are present and decode.

Usage
-----
    python scripts/audit_assets.py            # human-readable report
    python scripts/audit_assets.py --json     # machine-readable report

Exit code 0 = no problems found, 1 = problems found.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is a dev-only dependency
    print("Pillow is required: pip install pillow", file=sys.stderr)
    raise SystemExit(2)

REPO_ROOT = Path(__file__).resolve().parents[1]
INGREDIENT_DIR = REPO_ROOT / "ingredient"
SCENE_DIR = REPO_ROOT / "fronted asset"

EXPECTED_STEMS: tuple[str, ...] = (
    "apple", "avocado", "bacon", "banana", "beef", "bell_pepper", "bok_choy", "bread",
    "broccoli", "butter", "cabbage", "carrot", "cauliflower", "celery", "cheese", "chicken",
    "chickpeas", "chili_pepper", "cilantro", "coffee", "corn", "cream", "cucumber",
    "curry_paste", "daikon_radish", "dark_chocolate", "egg", "eggplant", "flour", "garlic",
    "ginger", "green_beans", "honey", "kimchi", "lemon", "lettuce", "lotus_root", "milk",
    "miso", "mushroom", "napa_cabbage", "noodles", "oats", "onion", "orange", "pasta", "pear",
    "pork", "potato", "pumpkin", "rice", "salmon", "scallion", "shrimp", "soy_sauce", "spinach",
    "squid", "strawberry", "sweet_potato", "tofu", "tomato", "tortilla", "white_fish", "yogurt",
    "zucchini",
)

SCENE_ASSETS: tuple[str, ...] = (
    "kitchen_background_wide.png",
    "fridge_closed.png",
    "fridge_ajar.png",
    "fridge_open_empty.png",
    "basket_empty.png",
    "magic_mixing_bowl.png",
    "recipe_book_open_blank.png",
    "favorites_recipe_box_empty.png",
)

#: A cutout should be mostly transparent around the subject and have a solid core.
MIN_TRANSPARENT_RATIO = 0.02
MIN_OPAQUE_RATIO = 0.02


def _alpha_stats(path: Path) -> Dict[str, object]:
    """Open an image and report alpha / opacity statistics (read-only)."""
    with Image.open(path) as im:
        im = im.convert("RGBA")
        width, height = im.size
        alpha = im.getchannel("A")
        hist = alpha.histogram()
        total = width * height
        opaque = sum(hist[200:])
        transparent = sum(hist[:32])
        # Mean colour of the reasonably opaque pixels.
        px = im.load()
        step = max(1, min(width, height) // 64)
        rs = gs = bs = n = 0
        for y in range(0, height, step):
            for x in range(0, width, step):
                r, g, b, a = px[x, y]
                if a >= 200:
                    rs += r
                    gs += g
                    bs += b
                    n += 1
        mean = [round(rs / n), round(gs / n), round(bs / n)] if n else None
        return {
            "width": width,
            "height": height,
            "mode": im.mode,
            "opaque_ratio": round(opaque / total, 4),
            "transparent_ratio": round(transparent / total, 4),
            "mean_opaque_rgb": mean,
        }


def _decode(path: Path) -> tuple[bool, str]:
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            im.load()
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def audit() -> Dict[str, object]:
    problems: List[str] = []

    # --- 1. filename completeness ----------------------------------------------------
    present = sorted(p.name for p in INGREDIENT_DIR.glob("*.png")) if INGREDIENT_DIR.is_dir() else []
    stems = [p[:-4] for p in present]
    duplicates = sorted({s for s in stems if stems.count(s) > 1})
    missing = [s for s in EXPECTED_STEMS if s not in stems]
    orphans = [s for s in stems if s not in EXPECTED_STEMS]
    if missing:
        problems.append(f"missing ingredient files: {missing}")
    if duplicates:
        problems.append(f"duplicate ingredient stems: {duplicates}")
    if orphans:
        problems.append(f"unexpected ingredient files: {orphans}")

    # --- 2/3. decode + alpha ---------------------------------------------------------
    ingredient_report: Dict[str, Dict[str, object]] = {}
    no_alpha: List[str] = []
    flat_cutouts: List[str] = []
    for stem in EXPECTED_STEMS:
        path = INGREDIENT_DIR / f"{stem}.png"
        if not path.is_file():
            continue
        ok, err = _decode(path)
        if not ok:
            problems.append(f"{stem}.png does not decode: {err}")
            continue
        stats = _alpha_stats(path)
        ingredient_report[stem] = stats
        if float(stats["transparent_ratio"]) < MIN_TRANSPARENT_RATIO:
            no_alpha.append(stem)
        if float(stats["opaque_ratio"]) < MIN_OPAQUE_RATIO:
            flat_cutouts.append(stem)
    if no_alpha:
        problems.append(f"no meaningful transparent region (not a cutout): {no_alpha}")
    if flat_cutouts:
        problems.append(f"no meaningful opaque subject: {flat_cutouts}")

    # --- 4. milk.png sanity -----------------------------------------------------------
    milk = ingredient_report.get("milk")
    milk_ok = bool(milk) and float(milk["opaque_ratio"]) >= MIN_OPAQUE_RATIO
    if milk and milk_ok:
        mean = milk["mean_opaque_rgb"] or [0, 0, 0]
        # Milk should read as a light, low-saturation (near-white / creamy) colour.
        milk_ok = min(mean) >= 150 and (max(mean) - min(mean)) <= 70
    if not milk_ok:
        problems.append("milk.png does not visibly contain opaque milk")

    # --- 5. scene assets ---------------------------------------------------------------
    scene_report: Dict[str, Dict[str, object]] = {}
    for name in SCENE_ASSETS:
        path = SCENE_DIR / name
        if not path.is_file():
            problems.append(f"missing scene asset: {name}")
            continue
        ok, err = _decode(path)
        if not ok:
            problems.append(f"{name} does not decode: {err}")
            continue
        with Image.open(path) as im:
            scene_report[name] = {
                "width": im.width,
                "height": im.height,
                "mode": im.mode,
            }

    return {
        "ingredient_dir": str(INGREDIENT_DIR),
        "scene_dir": str(SCENE_DIR),
        "expected_ingredient_count": len(EXPECTED_STEMS),
        "present_ingredient_count": len(stems),
        "missing": missing,
        "duplicates": duplicates,
        "orphans": orphans,
        "no_alpha_cutouts": no_alpha,
        "flat_cutouts": flat_cutouts,
        "milk": milk,
        "milk_ok": bool(milk_ok),
        "ingredients": ingredient_report,
        "scene_assets": scene_report,
        "scene_expected": len(SCENE_ASSETS),
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the raw report as JSON")
    args = parser.parse_args()

    report = audit()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=== ingredient/ ===")
        print(f"expected : {report['expected_ingredient_count']}")
        print(f"present  : {report['present_ingredient_count']}")
        print(f"missing  : {report['missing'] or 'none'}")
        print(f"duplicate: {report['duplicates'] or 'none'}")
        print(f"unexpected: {report['orphans'] or 'none'}")
        print(f"not-cutouts: {report['no_alpha_cutouts'] or 'none'}")
        print(f"empty cutouts: {report['flat_cutouts'] or 'none'}")
        print(f"milk.png : {report['milk']}  ok={report['milk_ok']}")
        print()
        print("=== fronted asset/ ===")
        print(f"expected : {report['scene_expected']}")
        for name, info in report["scene_assets"].items():  # type: ignore[union-attr]
            print(f"  {name}: {info['width']}x{info['height']} {info['mode']}")
        print()
        print("=== problems ===")
        problems = report["problems"]
        print("\n".join(f"  - {p}" for p in problems) if problems else "  none")

    return 1 if report["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
