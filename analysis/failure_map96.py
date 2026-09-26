"""96-game failure map on ONE population (validation_train96): F0 wins over 3 seeds (LQD_F0, actual orders recovered per seed) +
failure stage / dead-loop / wrong-object from the step-logged F0LOG96 seed-1 pass + rescue evidence from ctrl21 (train48 subset)."""
import json, re, collections, os
R = "/net/scratch/ymeng3/bos_alfworld"; H = "/net/scratch/ymeng3/bos_screens/hag"
orders = {s: json.load(open(f"{H}/game_order_train96_seed{s}.json"))["games_actual"] for s in (1, 2, 3)}
F0 = {s: json.load(open(f"{R}/results/LQD_F0_seed{s}.json")) for s in (1, 2, 3)}
wins = collections.defaultdict(list)
for s in (1, 2, 3):
    for g, w in zip(orders[s], F0[s]["won"]): wins[g].append(int(w))
L = json.load(open(f"{R}/results/F0LOG96_seed1.json")); LG = dict(zip(L["games_actual"], L["traj"])); LW = dict(zip(L["games_actual"], L["won"]))
def stage(g, tr):
    acts = [s["action"] for s in tr]; obs = [s["obs"] for s in tr]; parts = g.split('/')[-3].split('-'); obj = parts[1].lower(); tt = parts[0]
    picked = [(a, o) for a, o in zip(acts, obs) if a.startswith("take") and "You pick up" in o]
    wrong = any(re.sub(r"\s*\d+$", "", a.split(" from ")[0].replace("take ", "")).replace(" ", "") != obj for a, o in picked) if picked else False
    proc = any(re.match(r"(heat|cool|clean) ", a) and re.search(r"You (heat|cool|clean)", o) for a, o in zip(acts, obs))
    placed = any(re.match(r"(move|put) ", a) and ("You move" in o or "You put" in o) for a, o in zip(acts, obs))
    dead = sum(1 for s in tr if not s["admissible"])
    needs = tt in ("pick_heat_then_place_in_recep", "pick_cool_then_place_in_recep", "pick_clean_then_place_in_recep")
    st = "never_picked" if not picked else "picked_not_processed" if needs and not proc else "not_placed" if not placed else "placed_but_lost"
    return st, dead, wrong
C = json.load(open(f"{R}/results/XS_ctrl21_C_seed1.json")); meta = json.load(open(f"{R}/fd/meta.json")); ev = {}
for t in ["FD_ctrl"] + [f"FD_hint{k}" for k in range(4)]:
    d = json.load(open(f"{R}/results/{t}_seed1.json")); ev[t] = dict(zip(d["games_actual"], d["won"]))
rows = {}
for g in orders[1]:
    tr = LG.get(g, []); w3 = wins[g]; st, dead, wrong = stage(g, tr) if tr else ("?", 0, False)
    rows[g] = {"tt": g.split('/')[-3].split('-')[0], "f0_wins3": sum(w3), "f0log_won": int(LW.get(g, 0)), "stage": "won" if LW.get(g) else st, "dead": dead, "wrong_obj": wrong,
               "ctrl21_won": int(C["won"][C["games_actual"].index(g)]) if g in C["games_actual"] else None, "in_FD": g in meta,
               "rescued_any": (any(ev[t].get(g) for t in ev if t != "FD_ctrl") if g in meta else None), "ctrl_rescued": (bool(ev["FD_ctrl"].get(g)) if g in meta else None)}
json.dump(rows, open(f"{R}/fd/failure_map96.json", "w"), indent=1)
def cat(v):
    tot = v["f0_wins3"] + v["f0log_won"]
    if tot == 4: return "A  F0 wins in all 4 runs (solid)"
    if tot > 0: return "B  F0 wins in 1-3 of 4 runs (model CAN do it; harness unstable)"
    if v["rescued_any"]: return "C  F0 0/4, but a hint from the ctrl21 failure state rescued it (harness-recoverable)"
    if v["in_FD"]: return "E  F0 0/4, 4 hint strategies tried from ctrl21 state, NOT rescued (not yet recoverable)"
    if v["ctrl21_won"]: return "C' F0 0/4, but ctrl21 (a harness variant) won it (harness-recoverable)"
    return "D  F0 0/4, no rescue evidence (outside train48)"
print("=== 96 games: capability classes (F0 = bare harness, 4 runs: 3 LQD seeds + logged seed 1) ===")
for k, n in sorted(collections.Counter(cat(v) for v in rows.values()).items()): print(f"  {n:2d}  {k}")
print("\n=== where the logged F0 run (seed 1) loses: stage x dead-loop x wrong-object ===")
print(f"  {'stage':22s} {'n':>3s} {'dead>=5':>8s} {'wrong_obj':>10s} {'mean dead':>10s}")
for st, grp in sorted(collections.defaultdict(list, {k: [v for v in rows.values() if v['stage'] == k] for k in set(v['stage'] for v in rows.values())}).items()):
    print(f"  {st:22s} {len(grp):3d} {sum(v['dead']>=5 for v in grp):8d} {sum(v['wrong_obj'] for v in grp):10d} {sum(v['dead'] for v in grp)/len(grp):10.1f}")
print("\n=== by task type: n | F0 4/4 | F0 1-3 | F0 0/4 | of 0/4: rescued / tried-not-rescued / ctrl21-won / no evidence ===")
by = collections.defaultdict(lambda: [0]*8)
for v in rows.values():
    b = by[v["tt"]]; tot = v["f0_wins3"] + v["f0log_won"]; b[0] += 1; b[1] += tot == 4; b[2] += 0 < tot < 4; b[3] += tot == 0
    if tot == 0: b[4] += bool(v["rescued_any"]); b[5] += bool(v["in_FD"]) and not v["rescued_any"]; b[6] += (not v["in_FD"]) and bool(v["ctrl21_won"]); b[7] += (not v["in_FD"]) and not v["ctrl21_won"]
for k, b in sorted(by.items()): print(f"  {k:32s} {b[0]:2d} | {b[1]:2d} | {b[2]:2d} | {b[3]:2d} | {b[4]:2d} / {b[5]:2d} / {b[6]:2d} / {b[7]:2d}")
print("\n=== stage of the F0-0/4 games (logged run) ===")
for k, n in collections.Counter(v["stage"] for v in rows.values() if v["f0_wins3"] + v["f0log_won"] == 0).most_common(): print(f"  {n:2d}  {k}")
