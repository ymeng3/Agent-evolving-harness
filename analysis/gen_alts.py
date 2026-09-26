"""Failure-driven operator evolution, Stage 1+2 (2026-09-25): collect ctrl21 C failures, define a failure state per game, ask the
local model for K=4 DISTINCT alternative strategies per failure, write hints_k.json + replay prefixes + manifest."""
import json, re, sys, os, collections
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); import bos_alfworld as A
R = "/net/scratch/ymeng3/bos_alfworld"; K = 4; bb = A.Backbone(0.7)
r = json.load(open(f"{R}/results/XS_ctrl21_C_seed1.json")); rep = {}; man = []; hints = [{} for _ in range(K)]; meta = {}
for g, w, tr in zip(r["games_actual"], r["won"], r["traj"]):
    if w: continue
    acts = [s["action"] for s in tr]; obs = [s["obs"] for s in tr]; ttype = g.split("/")[-3]
    pick = [i for i, (a, o) in enumerate(zip(acts, obs)) if a.startswith("take") and "You pick up" in o]
    proc = [i for i, (a, o) in enumerate(zip(acts, obs)) if re.match(r"(heat|cool|clean) ", a) and ("You heat" in o or "You cool" in o or "You clean" in o)]
    t = (proc[0] if proc else pick[0] if pick else min(12, len(acts) - 2)); cls = "processed" if proc else "picked" if pick else "never_picked"
    rep[g] = acts[:t + 1]; man.append(g); meta[g] = {"tstar": t, "class": cls, "len": len(acts)}
    tail = "\n".join(f"step {i}: {acts[i]} -> {obs[i][:100]}" for i in range(max(0, t - 6), min(len(acts), t + 15)))
    p = (f"A text-game household agent FAILED this task. Task family: {ttype}. The agent's trajectory around the failure point (step {t}) was:\n{tail}\n\n"
         f"Propose {K} DISTINCT, concrete strategies the agent should follow from step {t} onward to complete the task. Each must be one or two sentences of "
         f"actionable advice (which places to go, what to do with the held object, what to avoid), not generic encouragement, and the {K} must differ in approach.\n"
         'Reply with ONLY a JSON list of strings.')
    resp, err = bb.call(p); m = re.search(r"\[.*\]", resp or "", re.S)
    try: L = json.loads(m.group(0)); assert len(L) >= K
    except Exception: L = ["Look for the target object in unexplored receptacles; open closed ones." , "Once holding the object, go directly to the target receptacle named in the task and place it there.", "If a heat/cool/clean step is required, stand at the appliance while holding the object and use 'heat/cool/clean OBJ with APPLIANCE'.", "Avoid repeating any action already tried; prefer places not visited yet."]
    for k in range(K): hints[k][g] = str(L[k])[:300]
    print(g.split("/")[-3][:45], cls, t, "|", str(L[0])[:80], flush=True)
json.dump(rep, open(f"{R}/fd/replay.json", "w")); open(f"{R}/fd/manifest.txt", "w").write("\n".join(man) + "\n"); json.dump(meta, open(f"{R}/fd/meta.json", "w"), indent=1)
for k in range(K): json.dump(hints[k], open(f"{R}/fd/hints_{k}.json", "w"), indent=1)
print("failures", len(man), collections.Counter(m_["class"] for m_ in meta.values()), "calls", bb.calls, "errors", bb.errors)
