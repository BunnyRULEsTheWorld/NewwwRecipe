#!/usr/bin/env python3
import argparse, json, math, statistics
from collections import Counter, defaultdict
from pathlib import Path

DIMENSIONS = ["culinary_knowledge_grounding","existing_culinary_precedent_analysis","innovation_delta_quality","mechanistic_plausibility","innovation_value","realization_quality"]
CATEGORIES = ["Conventional","Surface Innovation","Incremental Innovation","Structural Innovation","Transformative Innovation","Adversarial Trap"]

def load_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def load_jsonl(path): return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
def ranks(xs):
    order=sorted(range(len(xs)),key=lambda i:xs[i]); out=[0.0]*len(xs); i=0
    while i<len(order):
        j=i
        while j+1<len(order) and xs[order[j+1]]==xs[order[i]]: j+=1
        rank=(i+j+2)/2
        for k in range(i,j+1): out[order[k]]=rank
        i=j+1
    return out
def pearson(x,y):
    if len(x)<2:return None
    mx,my=sum(x)/len(x),sum(y)/len(y); dx=[a-mx for a in x];dy=[b-my for b in y]
    den=math.sqrt(sum(a*a for a in dx)*sum(b*b for b in dy))
    return None if den==0 else sum(a*b for a,b in zip(dx,dy))/den
def spearman(x,y): return pearson(ranks(x),ranks(y))
def qwk(g,p,n=5):
    if not g:return None
    O=[[0]*n for _ in range(n)]; hg=[0]*n;hp=[0]*n
    for a,b in zip(g,p): O[a-1][b-1]+=1;hg[a-1]+=1;hp[b-1]+=1
    obs=exp=0.0; N=len(g)
    for i in range(n):
        for j in range(n):
            w=((i-j)/(n-1))**2;obs+=w*O[i][j];exp+=w*(hg[i]*hp[j]/N)
    return None if exp==0 else 1-obs/exp
def macro_f1(g,p):
    vals=[]
    for c in CATEGORIES:
        tp=sum(a==c and b==c for a,b in zip(g,p));fp=sum(a!=c and b==c for a,b in zip(g,p));fn=sum(a==c and b!=c for a,b in zip(g,p))
        pr=tp/(tp+fp) if tp+fp else 0;rc=tp/(tp+fn) if tp+fn else 0
        vals.append(2*pr*rc/(pr+rc) if pr+rc else 0)
    return sum(vals)/len(vals)
def pairwise_acc(gold,pred):
    pos={x:i for i,x in enumerate(pred)};ok=tot=0
    for i in range(len(gold)):
        for j in range(i+1,len(gold)):
            if gold[i] in pos and gold[j] in pos: ok+=pos[gold[i]]<pos[gold[j]];tot+=1
    return ok/tot if tot else None

def main():
    ap=argparse.ArgumentParser();ap.add_argument("predictions");ap.add_argument("--data",default="data/cie_culinary_bench.json");ap.add_argument("--ranking-sets",default="validation_cases/ranking_sets.json");ap.add_argument("--output-json",default="results/metrics.json");ap.add_argument("--output-md",default="results/metrics.md");args=ap.parse_args()
    data=load_json(args.data); by={x["id"]:x for x in data}; rows=load_jsonl(args.predictions); valid=[r for r in rows if r.get("parsed") is not None and not r.get("error")]
    report={"rows_total":len(rows),"rows_parsed":len(valid),"parse_success_rate":len(valid)/len(rows) if rows else 0}
    case=[r for r in valid if r["task"]=="case_judge"]
    gcat=[];pcat=[]
    for r in case: gcat.append(by[r["item_id"]]["cie_annotation"]["innovation_category"]);pcat.append(r["parsed"].get("category"))
    report["classification"]={"n":len(case),"accuracy":sum(a==b for a,b in zip(gcat,pcat))/len(gcat) if gcat else None,"macro_f1":macro_f1(gcat,pcat) if gcat else None}
    traps=[(a,b) for a,b in zip(gcat,pcat) if a=="Adversarial Trap"]
    report["classification"]["adversarial_trap_accuracy"]=sum(a==b for a,b in traps)/len(traps) if traps else None
    c25=[b for r,b in zip(case,pcat) if r["item_id"]=="CIE-025"]
    report["classification"]["cie025_structural_or_transformative_rate"]=sum(x in ("Structural Innovation","Transformative Innovation") for x in c25)/len(c25) if c25 else None
    score_report={}
    for d in DIMENSIONS:
        g=[];p=[]
        for r in case:
            value=r["parsed"].get("scores",{}).get(d)
            if isinstance(value,int) and 1<=value<=5:g.append(by[r["item_id"]]["cie_annotation"]["scores"][d]);p.append(value)
        score_report[d]={"n":len(g),"mae":sum(abs(a-b) for a,b in zip(g,p))/len(g) if g else None,"within_1_accuracy":sum(abs(a-b)<=1 for a,b in zip(g,p))/len(g) if g else None,"exact_accuracy":sum(a==b for a,b in zip(g,p))/len(g) if g else None,"spearman":spearman(g,p),"qwk":qwk(g,p)}
    report["scoring"]=score_report
    grouped=defaultdict(list)
    for r in case:grouped[r["item_id"]].append(r["parsed"])
    modal=[];score_sds=[]
    for cid,items in grouped.items():
        cats=[x.get("category") for x in items];modal.append(Counter(cats).most_common(1)[0][1]/len(cats))
        for d in DIMENSIONS:
            vals=[x.get("scores",{}).get(d) for x in items];vals=[x for x in vals if isinstance(x,int)]
            if len(vals)>1:score_sds.append(statistics.pstdev(vals))
    report["consistency"]={"mean_modal_category_agreement":sum(modal)/len(modal) if modal else None,"mean_within_case_score_sd":sum(score_sds)/len(score_sds) if score_sds else None}
    sets={x["id"]:x for x in load_json(args.ranking_sets)["sets"]};ranks_rows=[r for r in valid if r["task"]=="ranking"]
    pa=[];sr=[]
    for r in ranks_rows:
        gold=sets[r["item_id"]]["gold_ordering"];pred=r["parsed"].get("ordering",[]);pa.append(pairwise_acc(gold,pred));pos={x:i for i,x in enumerate(pred)}
        if set(gold)==set(pred):sr.append(spearman(list(range(len(gold))),[pos[x] for x in gold]))
    report["ranking"]={"n":len(ranks_rows),"pairwise_accuracy":sum(x for x in pa if x is not None)/len([x for x in pa if x is not None]) if pa else None,"mean_spearman":sum(x for x in sr if x is not None)/len([x for x in sr if x is not None]) if sr else None}
    tiers=[r for r in valid if r["task"]=="quality_tier"];gold=["good","medium","bad"];vals=[]
    for r in tiers:vals.append(pairwise_acc(gold,r["parsed"].get("ordering",[])))
    report["discrimination"]={"n":len(tiers),"good_medium_bad_pairwise_accuracy":sum(x for x in vals if x is not None)/len([x for x in vals if x is not None]) if vals else None}
    Path(args.output_json).parent.mkdir(parents=True,exist_ok=True);Path(args.output_json).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# CIE-Bench Evaluation Metrics","",f"- Parsed: {report['rows_parsed']}/{report['rows_total']} ({report['parse_success_rate']:.1%})",f"- Classification accuracy: {report['classification']['accuracy']}",f"- Macro-F1: {report['classification']['macro_f1']}",f"- Trap accuracy: {report['classification']['adversarial_trap_accuracy']}",f"- Ranking pairwise accuracy: {report['ranking']['pairwise_accuracy']}",f"- Mean modal category agreement: {report['consistency']['mean_modal_category_agreement']}",f"- Mean within-case score SD: {report['consistency']['mean_within_case_score_sd']}","","See `metrics.json` for all six dimensions. No missing or unparsable row is silently excluded from the reported parse-success rate."]
    Path(args.output_md).write_text("\n".join(lines)+"\n",encoding="utf-8");print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
