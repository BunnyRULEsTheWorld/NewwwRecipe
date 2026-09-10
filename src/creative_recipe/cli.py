"""Thin CLI entry point (not the architectural center).

Usage:
    # offline demo with the fake provider
    python -m creative_recipe generate "chicken,coffee,cheese" --provider fake

    # real run via Hy3 (reads HY3_API_KEY / HY3_BASE_URL / HY3_MODEL from env)
    python -m creative_recipe generate "chicken,coffee,cheese"

Outputs Markdown by default; use --out path.json to export the raw result as JSON.
"""
from __future__ import annotations

import sys
from typing import List, Optional

import typer

from .config import Config
from .llm.base import LLMProvider
from .llm.fake import DemoProvider, FakeProvider
from .llm.hy3 import Hy3LLMClient
from .output.exporter import export
from .output.formatter import format_console, format_result
from .pipeline import run
from .types import Ingredient

app = typer.Typer(help="Creative Recipe AI — generate creative recipes evaluated by the CIE framework.")


def _build_provider(provider: str, cfg: Config) -> LLMProvider:
    if provider == "fake":
        return DemoProvider()
    # default: real Hy3 (key is required by from_env)
    return Hy3LLMClient.from_config(cfg)


@app.command()
def generate(
    ingredients: str = typer.Argument(..., help="Comma-separated ingredient list, e.g. 'chicken,coffee,cheese'"),
    constraints: Optional[str] = typer.Option(None, "--constraints", "-c", help="Optional constraints (cuisine, servings, dietary)."),
    num_concepts: int = typer.Option(5, "--num-concepts", "-n", help="N concepts to generate (default 5)."),
    top_k: int = typer.Option(2, "--top-k", "-k", help="Keep Top-K after Stage-A CIE (default 2)."),
    top_final: int = typer.Option(1, "--top-final", "-t", help="Final selection after Stage-B CIE (default 1)."),
    provider: str = typer.Option("hy3", "--provider", "-p", help="LLM provider: hy3 | fake."),
    out: Optional[str] = typer.Option(None, "--out", "-o", help="Write the raw result as JSON to this path."),
    console: bool = typer.Option(False, "--console", help="Print a compact console summary instead of Markdown."),
) -> None:
    ings = [Ingredient(name=s.strip()) for s in ingredients.split(",") if s.strip()]
    if not ings:
        typer.echo("Error: provide at least one ingredient.", err=True)
        raise typer.Exit(code=1)

    cfg = Config.from_env(require_key=(provider != "fake"))
    prov = _build_provider(provider, cfg)

    result = run(
        prov,
        ings,
        constraints=constraints,
        num_concepts=num_concepts,
        top_k_concepts=top_k,
        top_k_final=top_final,
    )

    if out:
        export(result, out)
        typer.echo(f"Wrote JSON result to {out}")
    if console:
        typer.echo(format_console(result))
    else:
        typer.echo(format_result(result))


@app.command()
def demo(
    out: Optional[str] = typer.Option(None, "--out", "-o", help="Write the raw result as JSON to this path."),
) -> None:
    """Run a built-in offline demo (chicken / coffee / cheese) using the DemoProvider."""
    ings = [Ingredient(name=n) for n in ["chicken", "coffee", "cheese"]]
    result = run(DemoProvider(), ings, num_concepts=1, top_k_concepts=1, top_k_final=1)
    if out:
        export(result, out)
        typer.echo(f"Wrote JSON result to {out}")
    typer.echo(format_result(result))


if __name__ == "__main__":
    app()
