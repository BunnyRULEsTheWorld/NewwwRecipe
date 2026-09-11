#!/usr/bin/env python3
import json, re, sys
from collections import Counter

data_path = sys.argv[1] if len(sys.argv) > 1 else "data/cie_culinary_bench.json"
source_path = sys.argv[2] if len(sys.argv) > 2 else "docs/source_registry.json"
data = json.load(open(data_path, encoding="utf-8"))
sources = json.load(open(source_path, encoding="utf-8"))
source_ids = {s["id"] for s in sources}
top = ["id","metadata","culinary_context","dish_information","innovation_trace","human_evaluation_signal","cie_annotation","benchmark_tags"]
categories = {"Conventional","Surface Innovation","Incremental Innovation","Structural Innovation","Transformative Innovation","Adversarial Trap"}
splits = {"competition_set","expert_set","baseline_set","adversarial_set"}
errors = []
ids = []
for i, c in enumerate(data):
    cid = c.get("id", f"index:{i}"); ids.append(cid)
    if list(c) != top: errors.append(f"{cid}: top-level key/order mismatch")
    if c.get("metadata",{}).get("id") != cid: errors.append(f"{cid}: metadata.id mismatch")
    if c.get("metadata",{}).get("data_split") not in splits: errors.append(f"{cid}: invalid split")
    cat = c.get("cie_annotation",{}).get("innovation_category")
    if cat not in categories: errors.append(f"{cid}: invalid category {cat}")
    mag = c.get("innovation_trace",{}).get("innovation_delta",{}).get("magnitude")
    if not isinstance(mag, int) or not 0 <= mag <= 5: errors.append(f"{cid}: invalid magnitude")
    scores = c.get("cie_annotation",{}).get("scores",{})
    if len(scores) != 6: errors.append(f"{cid}: score dimension count != 6")
    for k,v in scores.items():
        if not isinstance(v,int) or not 1 <= v <= 5: errors.append(f"{cid}: {k}={v}")
    tags = set(re.findall(r"\[(CIEA?\d{3}-S\d+)\]", json.dumps(c,ensure_ascii=False)))
    for tag in tags - source_ids: errors.append(f"{cid}: unresolved citation {tag}")
if len(ids) != len(set(ids)): errors.append("duplicate ids")
if len(data) != 30: errors.append(f"expected 30 cases, got {len(data)}")
expected = {"competition_set":9,"expert_set":11,"baseline_set":5,"adversarial_set":5}
if Counter(c["metadata"]["data_split"] for c in data) != Counter(expected): errors.append("split counts mismatch")
if errors:
    print("VALIDATION FAILED")
    print("\n".join("- "+e for e in errors))
    raise SystemExit(1)
print(f"VALIDATION PASSED: {len(data)} cases; {len(source_ids)} sources; all IDs, enums, score ranges and citations valid.")
