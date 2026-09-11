#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CIE-Culinary-Bench v1.1 — Benchmark Evaluation Pipeline (reliable runner, v1.2).

Reuses the project's ``Hy3LLMClient`` + ``Config`` (creative_recipe) as the
LLM-as-judge. Implements the three official tasks from ``docs/task_definition.md``:

  Task 1  Innovation Classification   (6-class)
  Task 2  CIE Dimension Scoring        (six 1-5 integer scores)
  Task 3  Pairwise Ranking             (order cases by a specified dimension)

Reliability + validity guarantees (v1.2 runner)
-----------------------------------------------
* **Incremental persistence**: every sample is written to ``predictions.jsonl``
  immediately after it returns (full current state rewritten each time, so a
  crash never loses prior results).
* **experiment_signature**: a stable hash over
  ``model, temperature, reasoning_effort, track, rubric_sha256, dataset_sha256,
  prompt_template_version, id_anonymization_version``. Every prediction row
  carries both ``experiment_signature`` and ``prompt_sha256``.
* **True resume validation**: a unit is skipped ONLY when
  ``existing.status == "ok"`` AND ``existing.prompt_sha256 == current`` AND
  ``existing.experiment_signature == current``. Otherwise it is re-run.
  (Legacy rows lacking ``experiment_signature`` are accepted only if their
  ``prompt_sha256`` matches, then re-stamped with the current signature.)
* **Hash-verified migration** (``--migrate-from``): completed rows from an older
  predictions file are carried over only after re-deriving their ``prompt_sha256``
  from the CURRENT prompts/config and confirming it equals the stored value.
  Rows that fail the check are dropped and re-run (never silently trusted).
* **Per-sample record**: sample_id, prediction, status (ok / api_error /
  parse_error), prompt_sha256, experiment_signature, timestamp, error,
  error_type, attempts, elapsed_ms, raw + parsed response.
* **Connection resilience**: transient connection failures use exponential
  backoff per unit; if 3 consecutive units ALL fail with connection errors the
  current round ABORTS (successful results are kept, resume possible later).
* **No gold leakage**: prompts use the ``closed_evidence`` view only. Case IDs
  are anonymized to neutral tokens inside the prompt and mapped back at scoring
  time, so labels such as ``CIE-A04`` cannot leak the Adversarial class.
* **experiment_complete gating**: final headline metrics (classification
  accuracy, mean Spearman, ranking accuracy) are published ONLY when 33/33
  units succeed. Partial runs emit ``experiment_complete: false`` and
  PARTIAL-marked metrics.

Outputs (under the run directory, written after the run):
  predictions.jsonl      one row per evaluation unit
  experiment_manifest.json  protocol + reproducibility metadata
  summary.json           classification / scoring / ranking / reliability metrics
  evaluation_report.md   human-readable evaluation report (PARTIAL banner if incomplete)
  error_analysis.md      failure cases + bias diagnosis

The dataset and gold labels are READ ONLY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# --------------------------------------------------------------------------- #
# Locate project root (creative-recipe-ai) for credentials + creative_recipe   #
# --------------------------------------------------------------------------- #
HERE = Path(__file__).resolve().parent            # .../CIE-Culinary-Bench/scripts
BENCH_ROOT = HERE.parent                          # .../CIE-Culinary-Bench
PROJECT_ROOT = BENCH_ROOT.parent                  # .../creative-recipe-ai
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")                # HY3_API_KEY / HY3_BASE_URL / HY3_MODEL

from creative_recipe.config import Config                 # noqa: E402
from creative_recipe.llm.hy3 import Hy3LLMClient          # noqa: E402

CATEGORIES = [
    "Conventional",
    "Surface Innovation",
    "Incremental Innovation",
    "Structural Innovation",
    "Transformative Innovation",
    "Adversarial Trap",
]
# Rank used for bias diagnostics (Adversarial Trap handled separately).
CAT_RANK = {
    "Conventional": 0,
    "Surface Innovation": 1,
    "Incremental Innovation": 2,
    "Structural Innovation": 3,
    "Transformative Innovation": 4,
}
DIMENSIONS = [
    "culinary_knowledge_grounding",
    "existing_culinary_precedent_analysis",
    "innovation_delta_quality",
    "mechanistic_plausibility",
    "innovation_value",
    "realization_quality",
]

# --------------------------------------------------------------------------- #
# Protocol / reproducibility constants (part of experiment_signature)          #
# --------------------------------------------------------------------------- #
PROMPT_TEMPLATE_VERSION = "v1.1.0"      # bump when system_prompt/case_prompt/ranking_prompt change
ID_ANONYMIZATION_VERSION = "v1"        # bump when build_id_maps/closed_view change
TRACK = "closed_evidence"               # main (closed) track; human_evidence_aware NOT implemented

BASELINE_PATH = BENCH_ROOT / "results" / "baseline_with_id" / "summary_with_id.json"


# --------------------------------------------------------------------------- #
# IO helpers                                                                    #
# --------------------------------------------------------------------------- #
def read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path: str):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def file_sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_from_text(text: str) -> dict:
    """Strip reasoning tags / markdown fences and extract the first JSON object."""
    if text is None:
        raise ValueError("empty response")
    text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < a:
        raise ValueError("no JSON object in response")
    return json.loads(text[a : b + 1])


# --------------------------------------------------------------------------- #
# experiment_signature                                                          #
# --------------------------------------------------------------------------- #
def compute_experiment_signature(*, model, temperature, reasoning_effort, track,
                                 rubric_sha256, dataset_sha256,
                                 prompt_template_version, id_anonymization_version) -> str:
    canon = {
        "model": model,
        "temperature": temperature,
        "reasoning_effort": reasoning_effort,
        "track": track,
        "rubric_sha256": rubric_sha256,
        "dataset_sha256": dataset_sha256,
        "prompt_template_version": prompt_template_version,
        "id_anonymization_version": id_anonymization_version,
    }
    return hashlib.sha256(
        json.dumps(canon, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# --------------------------------------------------------------------------- #
# ID anonymization (prevents id-encoded label leakage, e.g. CIE-A04 -> Adversarial)
# --------------------------------------------------------------------------- #
def build_id_maps(data, ranking_sets):
    real_ids = [x["id"] for x in data]
    for s in ranking_sets:
        real_ids.extend(s.get("case_ids", []))
    real_ids = list(dict.fromkeys(real_ids))
    real_to_token = {r: f"C{i:02d}" for i, r in enumerate(real_ids)}
    token_to_real = {t: r for r, t in real_to_token.items()}
    return real_to_token, token_to_real


def closed_view(case: dict, real_to_token: dict) -> dict:
    """Main-track (closed_evidence) view: no gold / human signal / metadata.

    The real id is replaced by a neutral token so category hints encoded in the
    id (e.g. the 'A' in CIE-A04) cannot leak the Adversarial label.
    """
    return {
        "case_id": real_to_token.get(case["id"], case["id"]),
        "culinary_context": case["culinary_context"],
        "dish_information": case["dish_information"],
        "innovation_trace": case["innovation_trace"],
    }


# --------------------------------------------------------------------------- #
# Prompts (reuse the frozen CIE rubric as the judge's authoritative rubric)    #
# --------------------------------------------------------------------------- #
def system_prompt(rubric: dict) -> str:
    rules = rubric.get("global_rules", [])
    rules_txt = "\n".join(f"- {r}" for r in rules)
    return (
        "你是 CIE-Culinary-Bench 的料理创新评审。只依据给定料理证据和 rubric 判断；"
        "品牌、价格、稀有食材、复杂术语与陌生程度都不能自动加分。"
        "Conventional 可有很高实现质量；magnitude 不等于 innovation value。"
        "不要透露隐藏思考过程，只输出严格 JSON。\n"
        f"允许类别：{json.dumps(CATEGORIES, ensure_ascii=False)}\n"
        f"RUBRIC:\n{json.dumps(rubric, ensure_ascii=False)}\n"
        f"全局规则：\n{rules_txt}"
    )


def case_prompt(view: dict) -> str:
    schema = {
        "category": "one of the six allowed categories",
        "scores": {d: 1 for d in DIMENSIONS},
        "reasoning": "<=180 Chinese characters",
        "failure_modes": [],
    }
    return (
        "TASK: 同时完成 Innovation Classification 与 CIE Dimension Scoring。\n"
        f"允许类别：{json.dumps(CATEGORIES, ensure_ascii=False)}\n"
        "评分必须逐维独立给出 1-5 整数，六维顺序固定；不得先给总分再反推。\n"
        f"OUTPUT SCHEMA:\n{json.dumps(schema, ensure_ascii=False)}\n"
        f"CASE:\n{json.dumps(view, ensure_ascii=False)}"
    )


def ranking_prompt(dimension: str, views: list) -> str:
    schema = {
        "dimension": dimension,
        "ordering": ["case-id-high-to-low"],
        "reasoning": "<=180 Chinese characters",
    }
    return (
        "TASK: 只按指定维度从高到低排序；case ID 必须各出现一次，不得遗漏或重复。\n"
        "不得使用餐厅名气、价格或技术数量替代指定维度。\n"
        f"指定维度：{dimension}\n"
        f"OUTPUT SCHEMA:\n{json.dumps(schema, ensure_ascii=False)}\n"
        f"CASES:\n{json.dumps(views, ensure_ascii=False)}"
    )


def build_messages(task, item_id, dimension, real_to_token, by_id, ranking_sets, system):
    """Reconstruct the exact request messages for a unit (used for prompt_sha256)."""
    if task == "case_judge":
        prompt = case_prompt(closed_view(by_id[item_id], real_to_token))
    else:  # ranking
        s = next(x for x in ranking_sets if x["id"] == item_id)
        views = [closed_view(by_id[x], real_to_token) for x in s["case_ids"]]
        prompt = ranking_prompt(s["dimension"], views)
    return [{"role": "system", "content": system}, {"role": "user", "content": prompt}]


def prompt_sha256_of(messages) -> str:
    return hashlib.sha256(json.dumps(messages, ensure_ascii=False).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Metrics (consistent with docs/task_definition.md)                            #
# --------------------------------------------------------------------------- #
def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            out[order[k]] = rank
        i = j + 1
    return out


def _pearson(x, y):
    if len(x) < 2:
        return None
    mx, my = sum(x) / len(x), sum(y) / len(y)
    dx = [a - mx for a in x]
    dy = [b - my for b in y]
    den = math.sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    return None if den == 0 else sum(a * b for a, b in zip(dx, dy)) / den


def spearman(x, y):
    return _pearson(_ranks(x), _ranks(y))


def kendall_tau_a(gold, pred):
    """Predefined order gold (high->low) vs predicted order (high->low)."""
    pos = {x: i for i, x in enumerate(pred)}
    conc = disc = 0
    n = len(gold)
    for i in range(n):
        for j in range(i + 1, n):
            gi, gj = gold[i], gold[j]
            if gi not in pos or gj not in pos:
                continue
            same_dir = (pos[gi] < pos[gj])  # pred also has gi above gj
            if same_dir:
                conc += 1
            else:
                disc += 1
    tot = conc + disc
    return None if tot == 0 else (conc - disc) / tot


def qwk(gold, pred, n=5):
    if not gold:
        return None
    O = [[0] * n for _ in range(n)]
    hg = [0] * n
    hp = [0] * n
    for a, b in zip(gold, pred):
        O[a - 1][b - 1] += 1
        hg[a - 1] += 1
        hp[b - 1] += 1
    obs = exp = 0.0
    N = len(gold)
    for i in range(n):
        for j in range(n):
            w = ((i - j) / (n - 1)) ** 2
            obs += w * O[i][j]
            exp += w * (hg[i] * hp[j] / N)
    return None if exp == 0 else 1 - obs / exp


def macro_f1(gold, pred):
    vals = []
    for c in CATEGORIES:
        tp = sum(a == c and b == c for a, b in zip(gold, pred))
        fp = sum(a != c and b == c for a, b in zip(gold, pred))
        fn = sum(a == c and b != c for a, b in zip(gold, pred))
        pr = tp / (tp + fp) if tp + fp else 0
        rc = tp / (tp + fn) if tp + fn else 0
        vals.append(2 * pr * rc / (pr + rc) if pr + rc else 0)
    return sum(vals) / len(vals)


def pairwise_acc(gold, pred):
    """gold, pred are high->low id lists. Score every pair (i above j)."""
    pos = {x: i for i, x in enumerate(pred)}
    ok = tot = 0
    for i in range(len(gold)):
        for j in range(i + 1, len(gold)):
            if gold[i] in pos and gold[j] in pos:
                ok += pos[gold[i]] < pos[gold[j]]
                tot += 1
    return ok / tot if tot else None


def _recall(gold, pred, c):
    tp = sum(a == c and b == c for a, b in zip(gold, pred))
    fn = sum(a == c and b != c for a, b in zip(gold, pred))
    return tp / (tp + fn) if (tp + fn) else None


def _trap_acc(gold, pred):
    pairs = [(a, b) for a, b in zip(gold, pred) if a == "Adversarial Trap"]
    return (sum(a == b for a, b in pairs) / len(pairs)) if pairs else None


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


# --------------------------------------------------------------------------- #
# Jobs                                                                          #
# --------------------------------------------------------------------------- #
def job_key(task, item_id, dimension, run):
    return (task, item_id, dimension, run)


def build_jobs(data, ranking_sets, limit, real_to_token, system):
    by_id = {x["id"]: x for x in data}
    jobs = []
    for case in data[:limit]:
        msgs = build_messages("case_judge", case["id"], None, real_to_token, by_id, ranking_sets, system)
        jobs.append(("case_judge", case["id"], case_prompt(closed_view(case, real_to_token)),
                     None, prompt_sha256_of(msgs)))
    n_rank = None if limit is None else max(1, limit // 10)
    for s in ranking_sets[:n_rank]:
        views = [closed_view(by_id[x], real_to_token) for x in s["case_ids"]]
        msgs = build_messages("ranking", s["id"], s["dimension"], real_to_token, by_id, ranking_sets, system)
        jobs.append(("ranking", s["id"], ranking_prompt(s["dimension"], views),
                     s["dimension"], prompt_sha256_of(msgs)))
    return jobs


def run_job(job, client, system, args, token_to_real):
    task, item_id, prompt, dimension, job_sha = job
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    row = {
        "sample_id": f"{task}:{item_id}:{dimension or '-'}:0",
        "task": task,
        "item_id": item_id,
        "dimension": dimension,
        "run": 0,
        "config": None,  # filled by caller
        "prompt_sha256": job_sha,
        "experiment_signature": None,  # filled by caller
        "raw_response": None,
        "parsed": None,
        "status": None,
        "attempts": 0,
        "error": None,
        "error_type": None,
        "timestamp": None,
        "elapsed_ms": None,
    }
    last_err = None
    last_type = None
    for attempt in range(1, args.max_retries + 1):
        row["attempts"] = attempt
        row["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        kwargs = {"temperature": args.temperature, "timeout": args.timeout}
        if args.reasoning_effort:
            kwargs["extra_body"] = {"chat_template_kwargs": {"reasoning_effort": args.reasoning_effort}}
        start = time.time()
        try:
            raw = client.chat(messages, **kwargs)
            parsed = json_from_text(raw)
            row["raw_response"] = raw
            row["parsed"] = _remap_ranking(parsed, task, token_to_real)
            row["status"] = "ok"
            row["error"] = None
            row["error_type"] = None
            row["elapsed_ms"] = round((time.time() - start) * 1000)
            return row
        except Exception as exc:  # API or parse failure
            last_type = type(exc).__name__
            last_err = f"{last_type}: {exc}"
            row["elapsed_ms"] = round((time.time() - start) * 1000)
            if attempt < args.max_retries:
                time.sleep(args.retry_backoff * (2 ** (attempt - 1)))
    row["status"] = "api_error" if row["raw_response"] is None else "parse_error"
    row["error"] = last_err
    row["error_type"] = last_type
    return row


def _remap_ranking(parsed, task, token_to_real):
    """Map anonymized tokens back to real ids in ranking predictions."""
    if task != "ranking" or not parsed:
        return parsed
    ordering = parsed.get("ordering")
    if isinstance(ordering, list):
        parsed = dict(parsed)
        parsed["ordering"] = [token_to_real.get(x, x) for x in ordering]
    return parsed


# --------------------------------------------------------------------------- #
# Resume / migration validation                                                 #
# --------------------------------------------------------------------------- #
def load_and_validate_seed(seed_path, current_sig, real_to_token, by_id, ranking_sets, system):
    """Load completed (ok) units from ``seed_path`` and re-validate each.

    A row is carried over ONLY when:
      * status == "ok"
      * re-derived prompt_sha256 (from CURRENT prompts/config) == stored prompt_sha256
      * stored experiment_signature is None (legacy) OR == current_sig
    Rows that fail are dropped and will be re-run (never silently trusted).
    """
    rows = {}
    try:
        seed = read_jsonl(str(seed_path))
    except FileNotFoundError:
        return rows
    carried = dropped = 0
    for r in seed:
        if r.get("status") != "ok":
            continue
        try:
            msgs = build_messages(r["task"], r["item_id"], r.get("dimension"),
                                  real_to_token, by_id, ranking_sets, system)
        except Exception:
            dropped += 1
            continue
        sha = prompt_sha256_of(msgs)
        if sha != r.get("prompt_sha256"):
            dropped += 1
            continue
        stored_sig = r.get("experiment_signature")
        if stored_sig is not None and stored_sig != current_sig:
            dropped += 1
            continue
        r2 = dict(r)
        r2["experiment_signature"] = current_sig
        rows[job_key(r["task"], r["item_id"], r.get("dimension"), r.get("run", 0))] = r2
        carried += 1
    print(f"[seed] carried={carried} dropped={dropped} from {seed_path}", flush=True)
    return rows


# --------------------------------------------------------------------------- #
# Runner                                                                        #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="CIE-Culinary-Bench v1.1 reliable evaluation pipeline")
    ap.add_argument("--data", default=str(BENCH_ROOT / "data" / "cie_culinary_bench.jsonl"))
    ap.add_argument("--rubric", default=str(BENCH_ROOT / "schema" / "scoring_rubric.json"))
    ap.add_argument("--ranking-sets", default=str(BENCH_ROOT / "validation_cases" / "ranking_sets.json"))
    ap.add_argument("--output-dir", default=str(BENCH_ROOT / "results" / "closed_evidence_anonymous_v1"))
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None, help="limit #cases (for smoke tests)")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--reasoning-effort", default="no_think")
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--max-retries", type=int, default=3)
    ap.add_argument("--retry-backoff", type=float, default=8.0)
    ap.add_argument("--dry-run", action="store_true", help="build prompts only, no API call")
    ap.add_argument("--force", action="store_true", help="ignore existing predictions, re-run all")
    ap.add_argument("--migrate-from", default=None, help="seed ok units (hash-validated) from an older predictions file")
    ap.add_argument("--analyze", action="store_true", help="offline: compute metrics from existing predictions.jsonl (no API)")
    ap.add_argument("--abort-after-conn", type=int, default=3,
                    help="abort the round after N consecutive connection-failure units")
    args = ap.parse_args()

    data = read_jsonl(args.data)
    rubric = read_json(args.rubric)
    ranking_sets = read_json(args.ranking_sets)["sets"]
    by_id = {x["id"]: x for x in data}
    real_to_token, token_to_real = build_id_maps(data, ranking_sets)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pred_path = out_dir / "predictions.jsonl"

    dataset_sha256 = file_sha256(args.data)
    rubric_sha256 = file_sha256(args.rubric)
    rubric_version = rubric.get("version", "unknown")
    model = Config.from_env(require_key=False).hy3_model if not args.dry_run else "hy3"
    experiment_signature = compute_experiment_signature(
        model=model,
        temperature=args.temperature,
        reasoning_effort=args.reasoning_effort,
        track=TRACK,
        rubric_sha256=rubric_sha256,
        dataset_sha256=dataset_sha256,
        prompt_template_version=PROMPT_TEMPLATE_VERSION,
        id_anonymization_version=ID_ANONYMIZATION_VERSION,
    )
    cfg_meta = {
        "model": model,
        "temperature": args.temperature,
        "reasoning_effort": args.reasoning_effort,
        "track": TRACK,
        "rubric": "schema/scoring_rubric.json (1-5, six dimensions)",
        "rubric_sha256": rubric_sha256,
        "dataset_sha256": dataset_sha256,
        "prompt_template_version": PROMPT_TEMPLATE_VERSION,
        "id_anonymization_version": ID_ANONYMIZATION_VERSION,
        "id_anonymized": True,
        "experiment_signature": experiment_signature,
        "runs": args.runs,
        "dry_run": args.dry_run,
        "judge_client": "creative_recipe.Hy3LLMClient",
        "runner": "benchmark_pipeline.py v1.2 (experiment_signature + true resume + conn-abort)",
    }
    started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    # ---- Offline analysis mode (no API) ---- #
    if args.analyze:
        if not pred_path.exists():
            print("ERROR: predictions.jsonl not found; run the pipeline first.", file=sys.stderr)
            return
        rows = read_jsonl(str(pred_path))
        expected = len(data) + len(ranking_sets)
        experiment_complete = (len(rows) == expected) and all(r.get("status") == "ok" for r in rows)
        summary = compute_summary(rows, by_id, ranking_sets, token_to_real)
        summary["experiment_complete"] = experiment_complete
        summary["partial"] = not experiment_complete
        summary["config"] = cfg_meta
        summary["dataset"] = {"path": args.data, "n_cases": len(data), "n_ranking_sets": len(ranking_sets)}
        (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_report(out_dir / "evaluation_report.md", summary, by_id, ranking_sets, experiment_complete)
        write_error_analysis(out_dir / "error_analysis.md", rows, by_id, ranking_sets, token_to_real, summary)
        write_manifest(out_dir / "experiment_manifest.json",
                       experiment_signature=experiment_signature, model=model,
                       dataset_path=args.data, dataset_sha256=dataset_sha256,
                       rubric_path=args.rubric, rubric_sha256=rubric_sha256,
                       rubric_version=rubric_version, prompt_template_version=PROMPT_TEMPLATE_VERSION,
                       track=TRACK, id_anon_enabled=True, id_anon_version=ID_ANONYMIZATION_VERSION,
                       temperature=args.temperature, reasoning_effort=args.reasoning_effort,
                       started_at=started_at, completed_at=None,
                       completed_units=sum(1 for r in rows if r.get("status") == "ok"),
                       failed_units=sum(1 for r in rows if r.get("status") != "ok"),
                       experiment_complete=experiment_complete, runner=cfg_meta["runner"])
        print(json.dumps(_headline(summary, experiment_complete), ensure_ascii=False))
        return

    client = Hy3LLMClient.from_env() if not args.dry_run else None
    system = system_prompt(rubric)

    if args.dry_run:
        jobs = build_jobs(data, ranking_sets, args.limit, real_to_token, system)
        dry_rows = []
        for job in jobs:
            task, item_id, prompt, dimension, job_sha = job
            messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
            dry_rows.append({
                "task": task, "item_id": item_id, "dimension": dimension,
                "request_messages": messages,
                "prompt_sha256": job_sha,
            })
        dry_path = out_dir / "dry_run_requests.jsonl"
        write_jsonl(dry_path, dry_rows)
        print(json.dumps({"status": "dry_run_complete", "jobs": len(jobs), "runs": args.runs,
                          "experiment_signature": experiment_signature,
                          "output": str(dry_path)}, ensure_ascii=False))
        return

    # ---- Live run with hash-validated resume / migration + incremental persistence ---- #
    jobs = build_jobs(data, ranking_sets, args.limit, real_to_token, system)
    total_units = len(jobs)

    # Seed completed units (migration source takes priority; else resume from own dir)
    rows = {}
    seeded_count = 0
    if args.migrate_from:
        rows = load_and_validate_seed(args.migrate_from, experiment_signature,
                                      real_to_token, by_id, ranking_sets, system)
    elif pred_path.exists() and not args.force:
        rows = load_and_validate_seed(pred_path, experiment_signature,
                                      real_to_token, by_id, ranking_sets, system)
    seeded_count = len(rows)
    # Persist seeded units immediately so the 16 good rows are safe before any new API call.
    if rows:
        write_jsonl(pred_path, list(rows.values()))
        print(f"[seed] {seeded_count} unit(s) persisted to {pred_path}", flush=True)

    consecutive_conn = 0
    aborted = False
    for job in jobs:
        task, item_id, _, dimension, job_sha = job
        k = job_key(task, item_id, dimension, 0)
        existing = rows.get(k)
        if (existing is not None and existing.get("status") == "ok"
                and existing.get("prompt_sha256") == job_sha
                and (existing.get("experiment_signature") is None
                     or existing.get("experiment_signature") == experiment_signature)):
            continue  # validated skip (true resume)
        row = run_job(job, client, system, args, token_to_real)
        row["config"] = cfg_meta
        row["experiment_signature"] = experiment_signature
        rows[k] = row
        # persist immediately (crash-safe: full current state on disk every sample)
        write_jsonl(pred_path, list(rows.values()))
        is_conn = "ConnectionError" in (row.get("error_type") or "")
        if row["status"] in ("api_error", "parse_error"):
            if is_conn:
                consecutive_conn += 1
            else:
                consecutive_conn = 0
        else:
            consecutive_conn = 0
        print(f"[{row['status']:>9}] {row['sample_id']} "
              f"(attempts={row['attempts']}, {row['elapsed_ms']}ms, conn_streak={consecutive_conn})", flush=True)
        if consecutive_conn >= args.abort_after_conn:
            aborted = True
            print(f"ABORT: {consecutive_conn} consecutive connection-failure units. "
                  f"Successful results retained; resume later.", flush=True)
            break

    all_rows = list(rows.values())
    experiment_complete = (len(all_rows) == total_units) and all(r.get("status") == "ok" for r in all_rows)
    completed_at = time.strftime("%Y-%m-%dT%H:%M:%S%z") if experiment_complete else None

    summary = compute_summary(all_rows, by_id, ranking_sets, token_to_real)
    summary["experiment_complete"] = experiment_complete
    summary["partial"] = not experiment_complete
    summary["aborted"] = aborted
    summary["config"] = cfg_meta
    summary["dataset"] = {"path": args.data, "n_cases": len(data), "n_ranking_sets": len(ranking_sets)}
    summary["resume"] = {"previously_completed": seeded_count, "rerun_this_session": total_units - seeded_count}
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(out_dir / "evaluation_report.md", summary, by_id, ranking_sets, experiment_complete)
    write_error_analysis(out_dir / "error_analysis.md", all_rows, by_id, ranking_sets, token_to_real, summary)
    write_manifest(out_dir / "experiment_manifest.json",
                   experiment_signature=experiment_signature, model=model,
                   dataset_path=args.data, dataset_sha256=dataset_sha256,
                   rubric_path=args.rubric, rubric_sha256=rubric_sha256,
                   rubric_version=rubric_version, prompt_template_version=PROMPT_TEMPLATE_VERSION,
                   track=TRACK, id_anon_enabled=True, id_anon_version=ID_ANONYMIZATION_VERSION,
                   temperature=args.temperature, reasoning_effort=args.reasoning_effort,
                   started_at=started_at, completed_at=completed_at,
                   completed_units=sum(1 for r in all_rows if r.get("status") == "ok"),
                   failed_units=sum(1 for r in all_rows if r.get("status") != "ok"),
                   experiment_complete=experiment_complete, runner=cfg_meta["runner"])

    print(json.dumps(_headline(summary, experiment_complete), ensure_ascii=False))


# --------------------------------------------------------------------------- #
# Summary + report + error analysis                                            #
# --------------------------------------------------------------------------- #
def compute_summary(rows, by_id, ranking_sets, token_to_real):
    valid = [r for r in rows if r.get("parsed") is not None and not r.get("error")]
    api_errors = [r for r in rows if r.get("status") in ("api_error", "parse_error") or r.get("error")]
    retry_total = sum(max(0, (r.get("attempts") or 1) - 1) for r in rows)
    summary = {
        "rows_total": len(rows),
        "rows_parsed": len(valid),
        "rows_failed": len(api_errors),
        "parse_success_rate": (len(valid) / len(rows)) if rows else 0.0,
        "api_failure_count": len(api_errors),
        "retry_count": retry_total,
    }

    # --- Task 1 + 2: classification & scoring (one row per case) --- #
    case_rows = [r for r in valid if r["task"] == "case_judge"]
    gcat, pcat = [], []
    for r in case_rows:
        gcat.append(by_id[r["item_id"]]["cie_annotation"]["innovation_category"])
        pcat.append(r["parsed"].get("category"))
    acc = sum(a == b for a, b in zip(gcat, pcat)) / len(gcat) if gcat else None
    summary["classification"] = {
        "n": len(case_rows),
        "accuracy": acc,
        "macro_f1": macro_f1(gcat, pcat) if gcat else None,
        "per_class_recall": {c: _recall(gcat, pcat, c) for c in CATEGORIES},
        "confusion_matrix": _confusion(gcat, pcat),
        "adversarial_trap_accuracy": _trap_acc(gcat, pcat),
    }
    c25 = [b for a, b in zip(case_rows, pcat) if a["item_id"] == "CIE-025"]
    summary["classification"]["cie025_structural_or_transformative_rate"] = (
        sum(x in ("Structural Innovation", "Transformative Innovation") for x in c25) / len(c25) if c25 else None
    )

    # --- Task 2: per-dimension scoring correlation --- #
    dim_report = {}
    spear_list = []
    for d in DIMENSIONS:
        g, p = [], []
        for r in case_rows:
            val = r["parsed"].get("scores", {}).get(d)
            if isinstance(val, int) and 1 <= val <= 5:
                g.append(by_id[r["item_id"]]["cie_annotation"]["scores"][d])
                p.append(val)
        rho = spearman(g, p)
        dim_report[d] = {
            "n": len(g),
            "mae": (sum(abs(a - b) for a, b in zip(g, p)) / len(g)) if g else None,
            "within_1_accuracy": (sum(abs(a - b) <= 1 for a, b in zip(g, p)) / len(g)) if g else None,
            "exact_accuracy": (sum(a == b for a, b in zip(g, p)) / len(g)) if g else None,
            "spearman": rho,
            "qwk": qwk(g, p),
        }
        if rho is not None:
            spear_list.append(rho)
    summary["scoring"] = {
        "dimensions": dim_report,
        "mean_spearman": _mean(spear_list),
        "min_spearman": min(spear_list) if spear_list else None,
        "max_spearman": max(spear_list) if spear_list else None,
        "mean_mae": _mean([dim_report[d]["mae"] for d in DIMENSIONS]),
    }

    # --- Task 3: pairwise ranking --- #
    sets = {x["id"]: x for x in ranking_sets}
    rank_rows = [r for r in valid if r["task"] == "ranking"]
    pa, sr, kt = [], [], []
    for r in rank_rows:
        gold = sets[r["item_id"]]["gold_ordering"]
        pred = r["parsed"].get("ordering", [])
        pa.append(pairwise_acc(gold, pred))
        if set(gold) == set(pred):
            pos = {x: i for i, x in enumerate(pred)}
            sr.append(spearman(list(range(len(gold))), [pos[x] for x in gold]))
            kt.append(kendall_tau_a(gold, pred))
    summary["ranking"] = {
        "n": len(rank_rows),
        "pairwise_accuracy": _mean(pa),
        "mean_spearman": _mean(sr),
        "mean_kendall_tau_a": _mean(kt),
    }

    # --- Consistency (only meaningful when runs >= 2) --- #
    if len({r["run"] for r in rows}) >= 2:
        summary["consistency"] = _consistency(case_rows)
    return summary


def _confusion(gold, pred):
    mat = {g: {p: 0 for p in CATEGORIES} for g in CATEGORIES}
    for a, b in zip(gold, pred):
        if a in mat and b in mat.get(a, {}):
            mat[a][b] += 1
    return {"categories": CATEGORIES, "matrix": mat}


def _consistency(case_rows):
    grouped = defaultdict(list)
    for r in case_rows:
        grouped[r["item_id"]].append(r["parsed"])
    modal, sds = [], []
    for cid, items in grouped.items():
        cats = [x.get("category") for x in items]
        if cats:
            modal.append(Counter(cats).most_common(1)[0][1] / len(cats))
        for d in DIMENSIONS:
            vals = [x.get("scores", {}).get(d) for x in items]
            vals = [v for v in vals if isinstance(v, int)]
            if len(vals) > 1:
                sds.append(statistics.pstdev(vals))
    return {
        "mean_modal_category_agreement": _mean(modal),
        "mean_within_case_score_sd": _mean(sds),
    }


def _headline(summary, experiment_complete):
    h = {
        "experiment_complete": experiment_complete,
        "rows": summary["rows_total"],
        "completed": summary["rows_parsed"],
        "failed": summary["rows_failed"],
    }
    if experiment_complete:
        h["classification_accuracy"] = summary["classification"]["accuracy"]
        h["macro_f1"] = summary["classification"]["macro_f1"]
        h["mean_dimension_spearman"] = summary["scoring"]["mean_spearman"]
        h["mean_dimension_mae"] = summary["scoring"]["mean_mae"]
        h["ranking_pairwise_accuracy"] = summary["ranking"]["pairwise_accuracy"]
        h["parse_success_rate"] = summary["parse_success_rate"]
        h["api_failure_count"] = summary["api_failure_count"]
        h["retry_count"] = summary["retry_count"]
    else:
        h["note"] = "PARTIAL — final metrics withheld until 33/33 units succeed"
        h["partial_classification_accuracy"] = summary["classification"]["accuracy"]
        h["partial_macro_f1"] = summary["classification"]["macro_f1"]
        h["partial_mean_dimension_spearman"] = summary["scoring"]["mean_spearman"]
        h["partial_ranking_pairwise_accuracy"] = summary["ranking"]["pairwise_accuracy"]
        h["parse_success_rate"] = summary["parse_success_rate"]
    return h


def write_manifest(path: Path, *, experiment_signature, model, dataset_path, dataset_sha256,
                   rubric_path, rubric_sha256, rubric_version, prompt_template_version,
                   track, id_anon_enabled, id_anon_version, temperature, reasoning_effort,
                   started_at, completed_at, completed_units, failed_units,
                   experiment_complete, runner):
    manifest = {
        "experiment_signature": experiment_signature,
        "model": model,
        "dataset": {"path": dataset_path, "version": dataset_sha256[:16], "sha256": dataset_sha256},
        "rubric": {"path": rubric_path, "version": rubric_version, "sha256": rubric_sha256},
        "prompt_template_version": prompt_template_version,
        "track": track,
        "id_anonymization": {"enabled": id_anon_enabled, "version": id_anon_version},
        "temperature": temperature,
        "reasoning_effort": reasoning_effort,
        "started_at": started_at,
        "completed_at": completed_at,
        "completed_units": completed_units,
        "failed_units": failed_units,
        "experiment_complete": experiment_complete,
        "runner": runner,
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, summary: dict, by_id, ranking_sets, experiment_complete):
    L = []
    L.append("# CIE-Culinary-Bench v1.1 — Evaluation Report\n")
    if not experiment_complete:
        L.append("> ⚠️ **PARTIAL RUN** — `experiment_complete: false`. "
                 "Only completed units are scored. The numbers below are **PARTIAL** and must "
                 "NOT be cited as final benchmark results. Final metrics are published only when "
                 "33/33 units succeed (see `experiment_manifest.json`).\n")
    L.append(f"- Judge: `{summary['config']['judge_client']}` (Hy3, OpenAI-compatible)")
    L.append(f"- Runner: {summary['config']['runner']}")
    L.append(f"- Rubric: {summary['config']['rubric']}")
    L.append(f"- Track: {summary['config']['track']} (IDs anonymized)  |  Temp: {summary['config']['temperature']}  |  Runs: {summary['config']['runs']}")
    L.append(f"- experiment_signature: `{summary['config']['experiment_signature']}`")
    L.append(f"- Dataset: {summary['dataset']['n_cases']} cases, {summary['dataset']['n_ranking_sets']} ranking sets")
    L.append(f"- Reliability: parse success {summary['parse_success_rate']:.1%} ({summary['rows_parsed']}/{summary['rows_total']}), "
             f"API failures {summary['api_failure_count']}, retries {summary['retry_count']}\n")

    L.append("## Task 1 — Innovation Classification\n")
    c = summary["classification"]
    tag = "" if experiment_complete else " _(PARTIAL)_"
    L.append(f"- **Accuracy**{tag}: {_pct(c['accuracy'])}")
    L.append(f"- **Macro-F1**{tag} (primary): {_fmt(c['macro_f1'])}")
    L.append(f"- **Adversarial Trap detection**: {_pct(c['adversarial_trap_accuracy'])}")
    L.append(f"- CIE-025 (luxury-signaling) mis-ranked as Structural/Transformative: {_pct(c['cie025_structural_or_transformative_rate'])}\n")
    L.append("Per-class recall:\n")
    for cat, rc in c["per_class_recall"].items():
        L.append(f"  - {cat}: {_pct(rc)}")
    L.append("")
    L.append("Confusion matrix (rows=gold, cols=pred):\n")
    L.append("| gold \\ pred | " + " | ".join(CATEGORIES) + " |")
    L.append("| --- | " + " | ".join(["---"] * len(CATEGORIES)) + " |")
    for g in CATEGORIES:
        row = c["confusion_matrix"]["matrix"].get(g, {})
        L.append(f"| {g} | " + " | ".join(str(row.get(p, 0)) for p in CATEGORIES) + " |")
    L.append("")

    L.append("## Task 2 — CIE Dimension Scoring (1–5)\n")
    L.append("Dimension score **correlation** (Spearman ρ, gold vs Hy3):\n")
    L.append("| Dimension | n | MAE | ±1 acc | Exact acc | Spearman ρ | QWK |")
    L.append("| --- | --- | --- | --- | --- | --- | --- |")
    for d, m in summary["scoring"]["dimensions"].items():
        L.append(f"| {d} | {m['n']} | {_fmt(m['mae'])} | {_pct(m['within_1_accuracy'])} | "
                 f"{_pct(m['exact_accuracy'])} | {_fmt(m['spearman'])} | {_fmt(m['qwk'])} |")
    s = summary["scoring"]
    L.append(f"\n- **Mean dimension Spearman ρ**{tag}: {_fmt(s['mean_spearman'])} "
             f"(min {_fmt(s['min_spearman'])}, max {_fmt(s['max_spearman'])})")
    L.append(f"- **Mean dimension MAE**: {_fmt(s['mean_mae'])}\n")

    L.append("## Task 3 — Pairwise Ranking\n")
    r = summary["ranking"]
    L.append(f"- **Pairwise accuracy**{tag}: {_pct(r['pairwise_accuracy'])}")
    L.append(f"- **Mean Spearman ρ**: {_fmt(r['mean_spearman'])}")
    L.append(f"- **Mean Kendall τ-a**: {_fmt(r['mean_kendall_tau_a'])}")
    L.append("")

    if "consistency" in summary:
        co = summary["consistency"]
        L.append("## Consistency (≥2 runs)\n")
        L.append(f"- Mean modal category agreement: {_pct(co['mean_modal_category_agreement'])}")
        L.append(f"- Mean within-case score SD: {_fmt(co['mean_within_case_score_sd'])}\n")

    # Protocol comparison vs the with-ID (leaky) baseline, when both available.
    cmp = _compare_baseline(summary)
    if cmp:
        L.append("## Protocol Comparison — anonymous (closed_evidence) vs with-ID baseline\n")
        L.append(f"- Baseline run (leaky, real IDs exposed): `results/baseline_with_id/` "
                 f"(id_anonymized={cmp['baseline_id_anonymized']})")
        L.append(f"- Classification accuracy: baseline {_pct(cmp['base_acc'])} → anonymous {_pct(c['accuracy'])}")
        L.append(f"- Adversarial Trap detection: baseline {_pct(cmp['base_trap'])} → anonymous {_pct(c['adversarial_trap_accuracy'])}")
        L.append(f"- Transformative recall: baseline {_pct(cmp['base_trans'])} → anonymous {_pct(c['per_class_recall']['Transformative Innovation'])}")
        L.append(f"- Mean dimension Spearman: baseline {_fmt(cmp['base_spear'])} → anonymous {_fmt(s['mean_spearman'])}")
        L.append("")

    L.append("> Full per-case detail (raw + parsed) is in `predictions.jsonl`. Failure cases and bias "
             "diagnosis are in `error_analysis.md`. Reproducibility metadata is in `experiment_manifest.json`.\n")
    L.append("---\n*Generated by scripts/benchmark_pipeline.py. Dataset unmodified; prompts use the "
             "closed_evidence view with anonymized IDs. Gold labels are never leaked into prompts.*")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def _compare_baseline(summary):
    try:
        base = read_json(str(BASELINE_PATH))
    except Exception:
        return None
    bc = base.get("classification", {})
    bs = base.get("scoring", {})
    return {
        "baseline_id_anonymized": base.get("config", {}).get("id_anonymized"),
        "base_acc": bc.get("accuracy"),
        "base_trap": bc.get("adversarial_trap_accuracy"),
        "base_trans": bc.get("per_class_recall", {}).get("Transformative Innovation"),
        "base_spear": bs.get("mean_spearman"),
    }


def write_error_analysis(path, rows, by_id, ranking_sets, token_to_real, summary):
    valid = [r for r in rows if r.get("parsed") is not None and not r.get("error")]
    case_rows = [r for r in valid if r["task"] == "case_judge"]
    rank_rows = [r for r in valid if r["task"] == "ranking"]
    sets = {x["id"]: x for x in ranking_sets}

    L = []
    L.append("# CIE-Culinary-Bench v1.1 — Error Analysis\n")
    if not summary.get("experiment_complete"):
        L.append(f"> ⚠️ **PARTIAL RUN** ({summary['rows_parsed']}/{summary['rows_total']} units ok). "
                 "Failure cases below are incomplete; re-run until 33/33 before drawing conclusions.\n")

    # 1. Classification errors
    L.append("## 1. Classification errors\n")
    cls_err = [(r, by_id[r["item_id"]]["cie_annotation"]["innovation_category"], r["parsed"].get("category"))
               for r in case_rows
               if r["parsed"].get("category") != by_id[r["item_id"]]["cie_annotation"]["innovation_category"]]
    if not cls_err:
        L.append("- None. All classification predictions match gold.\n")
    else:
        L.append(f"{len(cls_err)} misclassified case(s):\n")
        L.append("| ID | Gold | Pred | Reasoning (excerpt) |")
        L.append("| --- | --- | --- | --- |")
        for r, g, p in cls_err:
            reason = (r["parsed"].get("reasoning") or "")[:120]
            L.append(f"| {r['item_id']} | {g} | {p} | {reason} |")
        L.append("")

    # 2. Dimension score deviations (top 10 by total abs diff)
    L.append("## 2. Largest dimension-score deviations (top 10)\n")
    devs = []
    for r in case_rows:
        g = by_id[r["item_id"]]["cie_annotation"]["scores"]
        p = r["parsed"].get("scores", {})
        diffs = {d: abs(int(p.get(d, 0)) - int(g.get(d, 0))) for d in DIMENSIONS}
        total = sum(diffs.values())
        devs.append((r["item_id"], g, p, diffs, total))
    devs.sort(key=lambda x: x[4], reverse=True)
    if devs and devs[0][4] > 0:
        L.append("| ID | Total | per-dim (gold→pred) |")
        L.append("| --- | --- | --- |")
        for cid, g, p, diffs, total in devs[:10]:
            detail = ", ".join(f"{d.split('_')[0]}:{g[d]}→{p.get(d)}" for d in DIMENSIONS if diffs[d] > 0)
            L.append(f"| {cid} | {total} | {detail} |")
        L.append("")
    else:
        L.append("- No dimension deviations (perfect score match).\n")

    # 3. Ranking errors
    L.append("## 3. Ranking errors\n")
    rank_err = []
    for r in rank_rows:
        gold = sets[r["item_id"]]["gold_ordering"]
        pred = r["parsed"].get("ordering", [])
        pa = pairwise_acc(gold, pred)
        if pa is None or pa < 1.0:
            rank_err.append((r["item_id"], r["dimension"], gold, pred, pa))
    if not rank_err:
        L.append("- None. All ranking sets achieved perfect pairwise accuracy.\n")
    else:
        L.append(f"{len(rank_err)} imperfect ranking set(s):\n")
        L.append("| Set | Dimension | Gold (high→low) | Pred (high→low) | Pairwise acc |")
        L.append("| --- | --- | --- | --- | --- |")
        for sid, dim, gold, pred, pa in rank_err:
            L.append(f"| {sid} | {dim} | {' > '.join(gold)} | {' > '.join(pred)} | {_pct(pa)} |")
        L.append("")

    # 4. Bias diagnosis (heuristic, using gold vs pred category ranks)
    L.append("## 4. Bias diagnosis (heuristic)\n")
    bias = _bias_diagnosis(case_rows, by_id)
    L.append(f"- **Novelty / Technique Inflation** (pred ranked higher than gold on non-trap cases): "
             f"{bias['novelty_inflation']['count']} case(s)")
    if bias['novelty_inflation']['examples']:
        L.append(f"  - examples: {', '.join(bias['novelty_inflation']['examples'])}")
    L.append(f"- **Conventionality Bias** (pred ranked lower than gold): {bias['conventionality']['count']} case(s)")
    if bias['conventionality']['examples']:
        L.append(f"  - examples: {', '.join(bias['conventionality']['examples'])}")
    L.append(f"- **Adversarial Weirdness** (gold trap but pred not trap, or false alarm): "
             f"{bias['adversarial']['count']} case(s)")
    if bias['adversarial']['examples']:
        L.append(f"  - examples: {', '.join(bias['adversarial']['examples'])}")
    L.append(f"- **Ingredient Stacking** (gold low but pred high; flagged by benchmark_tags): "
             f"{bias['ingredient_stacking']['count']} case(s)")
    if bias['ingredient_stacking']['examples']:
        L.append(f"  - examples: {', '.join(bias['ingredient_stacking']['examples'])}")
    L.append("- **Note**: Ingredient-stacking uses `benchmark_tags` only as a diagnostic hint "
             "(not fed to the judge); `input_ingredients` is not provided at dataset top-level, so this "
             "signal is advisory and should be confirmed by manual review.\n")

    L.append("---\n*Heuristic bias diagnosis from gold vs prediction category ranks. "
             "See `summary.json` for quantitative metrics.*")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def _bias_diagnosis(case_rows, by_id):
    novelty = {"count": 0, "examples": []}
    conventionality = {"count": 0, "examples": []}
    adversarial = {"count": 0, "examples": []}
    ingredient = {"count": 0, "examples": []}
    for r in case_rows:
        cid = r["item_id"]
        gold = by_id[cid]["cie_annotation"]["innovation_category"]
        pred = r["parsed"].get("category")
        tags = by_id[cid].get("benchmark_tags", [])
        g_rank = CAT_RANK.get(gold)
        p_rank = CAT_RANK.get(pred)
        if gold == "Adversarial Trap":
            if pred != "Adversarial Trap":
                adversarial["count"] += 1
                adversarial["examples"].append(f"{cid}(pred={pred})")
        elif pred == "Adversarial Trap":
            adversarial["count"] += 1
            adversarial["examples"].append(f"{cid}(false_alarm)")
        else:
            if g_rank is not None and p_rank is not None:
                if p_rank > g_rank:
                    novelty["count"] += 1
                    novelty["examples"].append(f"{cid}({gold}→{pred})")
                elif p_rank < g_rank:
                    conventionality["count"] += 1
                    conventionality["examples"].append(f"{cid}({gold}→{pred})")
        if p_rank is not None and g_rank is not None and p_rank >= 3 and g_rank <= 1:
            if any(t in tags for t in ("ingredient_stacking", "technique_inflation", "stacking")):
                ingredient["count"] += 1
                ingredient["examples"].append(f"{cid}(tags={tags})")
    return {"novelty_inflation": novelty, "conventionality": conventionality,
            "adversarial": adversarial, "ingredient_stacking": ingredient}


def _fmt(x):
    return "n/a" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def _pct(x):
    return "n/a" if x is None else f"{x:.1%}"


if __name__ == "__main__":
    main()
