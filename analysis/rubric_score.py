import json, os, glob, statistics as st
R = "/net/scratch/ymeng3/bos_alfworld"
def sr(t, s):
    f = f"{R}/results/{t}_seed{s}.json"; return json.load(open(f))["success_rate"] * 100 if os.path.exists(f) else None
c = [sr("RB_C", 1), sr("RB_C", 2)]; print("C on held-out48:", c)
print(f"{'condition':10s} n  ops_net>=+3_both  mean_net  max_net  per-op")
for lab, name in (("A", "A raw"), ("B", "B fixed"), ("C", "C evolved")):
    nets = []
    for p in sorted(glob.glob(f"{R}/patches_rubric/RB{lab}*.py")):
        pid = os.path.basename(p)[:-3]; v = [sr(pid, 1), sr(pid, 2)]
        if None in v or None in c: continue
        nets.append((pid[:28], [round(a - b, 1) for a, b in zip(v, c)]))
    if not nets: print(name, "no results"); continue
    good = sum(min(n) >= 3 for _, n in nets); mean = st.mean(st.mean(n) for _, n in nets); mx = max(st.mean(n) for _, n in nets)
    print(f"{name:10s} {len(nets):d}  {good:d}                {mean:+5.1f}     {mx:+5.1f}   {nets}")
