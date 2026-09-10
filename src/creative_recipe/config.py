"""Configuration & environment handling.

Reads HY3_API_KEY / HY3_BASE_URL / HY3_MODEL from the environment.

Security contract:
  - HY3_API_KEY is REQUIRED and is only ever read from the environment — never hardcoded.
  - HY3_BASE_URL is read from the environment (region is configurable, NOT hardcoded).
  - A .env file is auto-loaded when present (via python-dotenv, if installed); the file is
    git-ignored and never committed.

Also exposes tunable pipeline parameters:
  num_concepts (N)    default 5   # RecipeConcepts generated
  top_k_concepts      default 2   # kept after Stage-A CIE
  top_k_final         default 1   # final selection after Stage-B CIE
"""
import os
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://tokenhub.tencentmaas.com/v1"
DEFAULT_MODEL = "hy3"


@dataclass
class Config:
    hy3_api_key: str
    hy3_base_url: str
    hy3_model: str
    num_concepts: int = 5
    top_k_concepts: int = 2
    top_k_final: int = 1

    @classmethod
    def from_env(cls, require_key: bool = True) -> "Config":
        # Best-effort load of a local .env file (no-op if missing or dotenv not installed).
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        api_key = os.getenv("HY3_API_KEY")
        if require_key and not api_key:
            raise RuntimeError(
                "HY3_API_KEY environment variable is required but not set. "
                "Copy .env.example to .env and fill it in (the .env file is never committed)."
            )
        return cls(
            hy3_api_key=api_key or "",
            hy3_base_url=os.getenv("HY3_BASE_URL", DEFAULT_BASE_URL),
            hy3_model=os.getenv("HY3_MODEL", DEFAULT_MODEL),
        )
