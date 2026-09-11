#!/usr/bin/env python3
"""Run CIE-Bench against Hy3 or another OpenAI-compatible endpoint.

No credential is stored in the repository. The official Hy3 deployment exposes
an OpenAI-compatible /v1/chat/completions endpoint.
"""
import argparse, hashlib, json, os, re, time, urllib.error, urllib.request
from collections import defaultdict
from pathlib import Path

CATEGORIES = ["Conventional","Surface Innovation","Incremental Innovation","Structural Innovation","Transformative Innovation","Adversarial Trap"]

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def closed_view(case, track):
    view = {
        "id": case["id"],
        "culinary_context": case["culinary_context"],
        "dish_information": case["dish_information"],
        "innovation_trace": case["innovation_trace"],
    }
    if track == "human_evidence_aware":
        view["human_evaluation_signal"] = case["human_evaluation_signal"]
    return view

def json_from_text(text):
    text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < a:
        raise ValueError("no JSON object in response")
    return json.loads(text[a:b+1])

def call_api(base_url, api_key, model, messages, temperature, reasoning_effort, timeout):
    payload = {
        "model": model, "messages": messages, "temperature": temperature,
        "top_p": 1.0,
        "chat_template_kwargs": {"reasoning_effort": reasoning_effort},
    }
    url = base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json", "Authorization":"Bearer "+api_key})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode())
    return body["choices"][0]["message"]["content"]

def system_prompt(rubric):
    return """你是 CIE-Culinary-Bench 的料理创新评审。只依据给定料理证据和 rubric 判断；品牌、价格、稀有食材、复杂术语与陌生程度都不能自动加分。Conventional 可有很高实现质量；magnitude 不等于 innovation value。不要透露隐藏思考过程，只输出严格 JSON。\nRUBRIC:\n""" + json.dumps(rubric, ensure_ascii=False)

def case_prompt(case_view):
    schema = {"category":"one controlled category","scores":{"culinary_knowledge_grounding":1,"existing_culinary_precedent_analysis":1,"innovation_delta_quality":1,"mechanistic_plausibility":1,"innovation_value":1,"realization_quality":1},"reasoning":"<=180 Chinese characters","failure_modes":[]}
    return "TASK: 同时完成 Innovation Classification 与 CIE Scoring。\n允许类别："+json.dumps(CATEGORIES,ensure_ascii=False)+"\nOUTPUT SCHEMA:\n"+json.dumps(schema,ensure_ascii=False)+"\nCASE:\n"+json.dumps(case_view,ensure_ascii=False)

def ranking_prompt(dimension, views):
    schema = {"dimension":dimension,"ordering":["case-id-high-to-low"],"reasoning":"<=180 Chinese characters"}
    return "TASK: 只按指定维度从高到低排序；case ID 必须各出现一次。不得使用餐厅名气、价格或技术数量替代维度。\nOUTPUT SCHEMA:\n"+json.dumps(schema,ensure_ascii=False)+"\nCASES:\n"+json.dumps(views,ensure_ascii=False)

def tier_prompt(case_view, candidates):
    schema = {"ordering":["candidate-id-high-to-low"],"reasoning":"<=180 Chinese characters"}
    return "TASK: 按料理创新评审质量从好到差排序三个候选回答，关注先例、delta、机制、风险与证据边界。\nOUTPUT SCHEMA:\n"+json.dumps(schema,ensure_ascii=False)+"\nCASE:\n"+json.dumps(case_view,ensure_ascii=False)+"\nCANDIDATES:\n"+json.dumps(candidates,ensure_ascii=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/cie_culinary_bench.json")
    ap.add_argument("--rubric", default="schema/scoring_rubric.json")
    ap.add_argument("--ranking-sets", default="validation_cases/ranking_sets.json")
    ap.add_argument("--quality-tiers", default="validation_cases/good_medium_bad_cases.jsonl")
    ap.add_argument("--task", choices=["case","ranking","quality_tier","all"], default="all")
    ap.add_argument("--track", choices=["closed_evidence","human_evidence_aware"], default="closed_evidence")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--output", default="results/hy3_predictions.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--base-url", default=os.getenv("CIE_API_BASE_URL", "http://127.0.0.1:8000/v1"))
    ap.add_argument("--api-key", default=os.getenv("CIE_API_KEY", "EMPTY"))
    ap.add_argument("--model", default=os.getenv("CIE_MODEL", "hy3"))
    ap.add_argument("--temperature", type=float, default=float(os.getenv("CIE_TEMPERATURE", "0.2")))
    ap.add_argument("--reasoning-effort", default=os.getenv("CIE_REASONING_EFFORT", "no_think"), choices=["no_think","low","high"])
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()
    data, rubric = read_json(args.data), read_json(args.rubric)
    by_id = {x["id"]: x for x in data}
    jobs = []
    if args.task in ("case","all"):
        for case in data[:args.limit]:
            jobs.append(("case_judge", case["id"], case_prompt(closed_view(case,args.track))))
    if args.task in ("ranking","all"):
        for s in read_json(args.ranking_sets)["sets"][:args.limit]:
            views = [closed_view(by_id[x],args.track) for x in s["case_ids"]]
            jobs.append(("ranking", s["id"], ranking_prompt(s["dimension"],views)))
    if args.task in ("quality_tier","all"):
        grouped = defaultdict(list)
        for row in read_jsonl(args.quality_tiers): grouped[row["case_id"]].append(row)
        for cid, rows in list(grouped.items())[:args.limit]:
            candidates = [{"candidate_id":r["quality"],"answer":r["mock_model_assessment"]} for r in rows]
            jobs.append(("quality_tier",cid,tier_prompt(closed_view(by_id[cid],args.track),candidates)))
    out = Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    system = system_prompt(rubric)
    config = {"model":args.model,"base_url":args.base_url,"temperature":args.temperature,"reasoning_effort":args.reasoning_effort,"track":args.track,"runs":args.runs,"dry_run":args.dry_run}
    with out.open("w",encoding="utf-8") as f:
        for run in range(args.runs):
            for task, item_id, prompt in jobs:
                messages=[{"role":"system","content":system},{"role":"user","content":prompt}]
                row={"task":task,"item_id":item_id,"run":run,"config":config,"prompt_sha256":hashlib.sha256(json.dumps(messages,ensure_ascii=False).encode()).hexdigest(),"parsed":None,"raw_response":None,"error":None}
                if args.dry_run:
                    row["request_messages"] = messages
                else:
                    start=time.time()
                    try:
                        row["raw_response"] = call_api(args.base_url,args.api_key,args.model,messages,args.temperature,args.reasoning_effort,args.timeout)
                        row["parsed"] = json_from_text(row["raw_response"])
                    except Exception as exc:
                        row["error"] = f"{type(exc).__name__}: {exc}"
                    row["elapsed_ms"] = round((time.time()-start)*1000)
                f.write(json.dumps(row,ensure_ascii=False)+"\n"); f.flush()
    print(json.dumps({"status":"dry_run_complete" if args.dry_run else "run_complete","jobs_per_run":len(jobs),"runs":args.runs,"rows":len(jobs)*args.runs,"output":str(out)},ensure_ascii=False))

if __name__ == "__main__": main()
