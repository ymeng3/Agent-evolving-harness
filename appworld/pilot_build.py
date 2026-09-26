"""AppWorld rescue pilot, steps 1-3: pick 10 partial failures from AW_F0full, locate the branch point, write replay prefixes + policy hints."""
import json, re, collections
R = "/net/scratch/ymeng3/bos_appworld"; r = json.load(open(f"{R}/results/AW_F0full_seed1.json"))
MUT = re.compile(r"apis\.(?!api_docs|supervisor)\w+\.(create|update|delete|send|add|remove|withdraw|pay|post|mark|reply|like|unlike|set|transfer|book|cancel|upload)\w*\(")
cands = []
for t, w, G, tr in zip(r["games"], r["won"], r["G"], r["traj"]):
    if w or G is None or G <= 0: continue
    acts = [s["code"] for s in tr]
    mut = [i for i, c in enumerate(acts) if MUT.search(c)]; errs = [i for i, s in enumerate(tr) if s["exec_error"]]
    t_b = mut[0] if mut else (errs[0] if errs else max(0, len(tr) - 2))   # branch BEFORE the first state-changing call
    fam = t.split("_")[0]; cands.append((fam, t, G, t_b, len(tr), mut[:1], errs[:2]))
picked = []; per_fam = collections.Counter()
for fam, t, G, t_b, n, mut, errs in sorted(cands, key=lambda x: -x[2]):
    if per_fam[fam] >= 2: continue
    per_fam[fam] += 1; picked.append((fam, t, G, t_b, n, mut, errs))
    if len(picked) == 10: break
rep = {}; meta = {}
for fam, t, G, t_b, n, mut, errs in picked:
    tr = r["traj"][r["games"].index(t)]; rep[t] = [s["code"] for s in tr[:t_b]]
    meta[t] = {"G_f0": G, "t_branch": t_b, "len": n, "first_mutating_step": mut, "first_error_steps": errs, "branch_code": tr[t_b]["code"][:200] if t_b < n else ""}
    print(f"{t:12s} G {G:.2f} len {n:2d} branch@{t_b:2d} first-mutating {mut} errs {errs} | {tr[t_b]['code'][:90]!r}")
json.dump(rep, open(f"{R}/pilot/replay.json", "w")); json.dump(meta, open(f"{R}/pilot/meta.json", "w"), indent=1); json.dump(list(rep), open(f"{R}/pilot/tasks10.json", "w"))
POL = {
 "docfirst": "Before calling any API that CHANGES state (create/update/delete/send/pay/request...), first list that app's APIs with apis.api_docs.show_api_descriptions(app_name=...), choose the ONE whose description matches the task's verb exactly (e.g. 'request money' is not 'send money'), read its doc with show_api_doc, and only then call it with the documented parameter names.",
 "verify": "Before calling apis.supervisor.complete_task(), re-read the task sentence and list every requirement in it (which action, who, amount, note/text, privacy/visibility, which app). For each one, check the API results you have already printed prove it was done as asked. If anything is missing or was done with the wrong action, fix it first; never mark the task complete with a wrong or partial action.",
}
for k, txt in POL.items(): json.dump({t: txt for t in rep}, open(f"{R}/pilot/hints_{k}.json", "w"))
print("picked", len(picked), "families", dict(per_fam))
