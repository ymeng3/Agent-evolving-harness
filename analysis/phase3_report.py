import json, os, re, glob
R = "/net/scratch/ymeng3/bos_alfworld"; P3 = f"{R}/patches_p3"; L = open(f"{P3}/phase3.log").read()
C = json.load(open(f"{P3}/cands_decision.json")); U = json.load(open(f"{P3}/units.json"))
print("STEP 1  candidate vs parent (paired, train48, seed 1):")
for k, v in C.items(): print(f"  {k}: C {v.get('C_wins')} vs parent {v.get('parent_wins')} wins | paired d {v.get('paired_d'):+d} | decompose: {v.get('decompose')}" if 'C_wins' in v else f"  {k}: missing")
print("\nSTEP 2  component credit (ON = candidate pass, OFF = unit removed; paired on the same games):")
print(f"  {'unit':22s} {'kind':7s} {'ON':>3s} {'OFF':>4s} {'d':>4s} {'n':>3s} {'halves':>10s}  decision   samples")
tot_used = 0; tot_fixed = 0
for k, v in U.items():
    if not C.get(v["cand"], {}).get("decompose"): continue
    m = [x for x in re.findall(rf"{re.escape(k)} (?:n=(\d+) |local )(\{{.*?\}})", L)]
    if not m: print(f"  {k:22s} {v['kind']:7s} no result"); continue
    n_last, js = m[-1]; d = json.loads(js); used = sum(int(a) for a, _ in m if a) if v["kind"] == "global" else 48
    if v["kind"] == "global": used = int(n_last)
    else:
        meta = f"{R}/probeL/p3_{k.replace(':','_')}_meta.json"; used = 48
        if os.path.exists(meta): M = json.load(open(meta)); used = round(sum(1 - m_["tstar"] / max(m_["len"], 1) for m_ in M.values()), 1)
    tot_used += used; tot_fixed += 48
    print(f"  {k:22s} {v['kind']:7s} {d.get('on',0):3d} {d.get('off',0):4d} {d.get('d',0):+4d} {d.get('n',0):3d} {str(d.get('halves')):>10s}  {d.get('decision'):10s} {used}")
print(f"  OFF episode-equivalents used: {tot_used} vs fixed-48 {tot_fixed} ({100*tot_used/max(tot_fixed,1):.0f}%)")
print("\nSTEP 4  window ablation (32 games, seed 1; ON = candidate pass on the same 32 games):")
for f in sorted(glob.glob(f"{R}/results/P3W_*_seed1.json")):
    d = json.load(open(f)); tag = d["tag"]; key = tag.split("_")[1]; on = json.load(open(f"{R}/results/P3C_{key}_seed1.json"))
    onm = dict(zip(on["games_actual"], on["won"])); offm = dict(zip(d["games_actual"], d["won"])); gs = [g for g in offm if g in onm]
    print(f"  {tag:28s} ON {sum(onm[g] for g in gs):2d} vs variant {sum(offm[g] for g in gs):2d} on {len(gs)} games (d {sum(onm[g]-offm[g] for g in gs):+d})")
