import json, os
R = "/net/scratch/ymeng3/bos_appworld"
CLS = {"shop": "e7f15ba_1 4242c97_1 dc5c5c6_1 d9987f6_1 20c1328_1 b6d1f70_1 953b296_1 690d51b_1 77bcb81_1 9871968_1 f86d850_1".split(),
       "cross": "9126bf0_1 f099b4c_1 3fcc458_1 1a79e37_1 e201314_1 a676f2a_1 c8f5f44_1 80acbaf_1 ffea2b5_1 a3ba388_1 33e202d_1 ce73d68_1 c1091c7_1".split(),
       "multi": "5800354_1 2e9b91e_1 3f3c139_1 7574325_1 09ac073_1 e52623a_1".split()}
TARGET = {"E1": "shop", "E2": "cross", "E3": "multi", "E123": None}
def wm(tag, s):
    f = f"{R}/results/{tag}_seed{s}.json"
    if not os.path.exists(f): return None
    d = json.load(open(f)); return {"w": dict(zip(d["games"], d["won"])), "err": d["api_errors"], "G": d["mean_G"]}
print("=== DISCOVERY-50 (baseline CH27_F0) ===")
print(f"{'interv':6s} seed  won  base  net | own-class rescued/broken | other-class rescued/broken | api_err")
for E in ("E1", "E2", "E3", "E123"):
    for s in (1, 2):
        d = wm(f"P1_{E}_disc", s); b = wm("CH27_F0", s)
        if not d or not b: print(f"{E:6s} {s}  missing"); continue
        own = CLS.get(TARGET[E], [])
        ro = sum(d["w"][t] and not b["w"][t] for t in own); bo = sum(b["w"][t] and not d["w"][t] for t in own)
        rx = sum(d["w"][t] and not b["w"][t] for t in d["w"] if t not in own); bx = sum(b["w"][t] and not d["w"][t] for t in d["w"] if t not in own)
        print(f"{E:6s} {s}   {sum(d['w'].values()):3d}  {sum(b['w'].values()):3d}  {sum(d['w'].values())-sum(b['w'].values()):+3d} |        {ro}/{bo} (of {len(own)})        |        {rx}/{bx}            | {d['err']}")
print("\n=== VALIDATION-50 (baseline VAL_F0) ===")
print(f"{'interv':6s} seed  won  base  net  rescued/broken  api_err")
for E in ("E1", "E2", "E3", "E123"):
    for s in (1, 2):
        d = wm(f"P1_{E}_val", s); b = wm("VAL_F0", s)
        if not d or not b: continue
        r = sum(d["w"][t] and not b["w"][t] for t in d["w"]); k = sum(b["w"][t] and not d["w"][t] for t in d["w"])
        print(f"{E:6s} {s}   {sum(d['w'].values()):3d}  {sum(b['w'].values()):3d}  {sum(d['w'].values())-sum(b['w'].values()):+3d}    {r}/{k}          {d['err']}")
for s in (1, 2):
    b = wm("VAL_F0", s); print(f"VAL_F0 s{s}: {sum(b['w'].values()) if b else 'missing'}")
