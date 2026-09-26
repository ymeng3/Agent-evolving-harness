import json, os
R = "/net/scratch/ymeng3/bos_alfworld"
def sr(t, s):
    f = f"{R}/results/{t}_seed{s}.json"; return json.load(open(f))["success_rate"] * 100 if os.path.exists(f) else None
S = json.load(open(f"{R}/fd/stage5.json"))
print("THREE-AGENT COMPARISON on held-out 48 games (never used for discovery/selection), seeds 1,2:")
for t, lab in (("HO_C", "original (ctrl21 C)"), ("HO_SO", "search-only best-of-6 (selected on train48)"), ("HO_OURS", "operators + credit-guided inheritance")):
    v = [sr(t, 1), sr(t, 2)]; print(f"  {lab:48s} {v}  mean {sum(x for x in v if x is not None)/max(1,sum(x is not None for x in v)):.1f}")
print("committed operators:", [os.path.basename(p) for p in S["committed"]], "| OURS:", os.path.basename(S["ours"]))
