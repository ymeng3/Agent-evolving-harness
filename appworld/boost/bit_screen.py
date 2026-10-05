"""BIT Unit E: screening (docs/design/BIT_IMPLEMENTATION_PLAN.md Unit E, BOOSTED_INTERVENTION_TREES_v0.md section 3).
Every valid candidate spec (cands JSONL from bit_propose.py; --refs spec JSONs are scored too, marked "ref", never kept) is compiled and
simulated over the base discovery episodes (not crashed, no replayed step); phi_e = 1 if it fired anywhere in episode e. Per candidate:
fire rates, the within-task IC with a task-bootstrap CI, the same-task pairwise split gain (gain_within, 0 unless it fires more on losers),
the residual gain over the memory tree gain_raw = (sum_fired g)^2 / (sum_fired h + lam) with g, h of the trie node at the fire depth,
steps left at the fire, hook errors, rates on tasks never shown to the proposer, and memorization flags. Near-duplicates (Jaccard of fired
eid sets >= --jaccard) are dropped in favour of the higher gain_within; kept = top --k-within by gain_within + top --k-raw by gain_raw
among candidates with P(fire|won) <= --max-won-fire.
usage: python boost/bit_screen.py --cands cands_P1.jsonl[,cands_P2.jsonl] --runs A.json,B.json --instr instructions_all100.json
                                  --tree bit/<R>/tree.json --out bit/<R>/screen.json [--refs boost/bit_refs/D10_ref.json,...]
                                  [--k-within 4 --k-raw 4 --max-won-fire 0.05 --lam 1.0 --jaccard 0.8 --workers 6 --timeout 120]"""
import argparse, ast, collections, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bit_common import load_episodes, make_pairs, pair_gain, within_ic, beta_stats
from bit_tree import build_tries, node_at


def _norm(s):
    return " ".join((s or "").lower().split())


_QUOTED = re.compile(r"'([^']{4,200})'|\"([^\"]{4,200})\"|“([^”]{4,200})”")


def _literals(spec):
    """string / number literals of the detect source and the note: (strings, numbers). Quoted phrases inside a string (e.g. a note that
    quotes the task) count as strings of their own."""
    strs, nums = [], []
    try: tree = ast.parse(spec.get("detect_src") or "")
    except SyntaxError: tree = None
    vals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)] if tree else []
    vals.append(spec.get("note") or "")
    for v in vals:
        if isinstance(v, bool): continue
        if isinstance(v, (int, float)): nums.append(str(v)); continue
        if not isinstance(v, str): continue
        strs.append(v); strs += [x for t in _QUOTED.findall(v) for x in t if x]
        nums += re.findall(r"(?<!\d)\d{3,}(?!\d)", re.sub(r"\{\d*,?\d*\}", " ", v))   # regex quantifiers {1,200} are not data
    return strs, nums


def memo_hits(spec, shown_text):
    """>= 3-word string literals / >= 3-digit numbers of the spec that occur in the shown cases' text (normalized, case-insensitive).
    Round numbers (multiples of 100: thresholds like 200 = the logged output length) are not counted."""
    strs, nums = _literals(spec); hits = []
    for s in strs:
        n = _norm(s)
        if len(n.split()) >= 3 and n in shown_text and n not in hits: hits.append(n)
    for x in nums:
        digits = re.sub(r"\D", "", x.split(".")[0])
        if len(digits) >= 3 and int(digits) % 100 != 0 and re.search(r"(?<!\d)" + re.escape(x) + r"(?!\d)", shown_text) and x not in hits: hits.append(x)
    return hits


def _rates(phi, won):
    phi = np.asarray(phi, float); won = np.asarray(won, bool); n = len(phi)
    return {"n": n, "n_fire": int(phi.sum()), "s": float(phi.mean()) if n else 0.0,
            "p_fire_lost": float(phi[~won].mean()) if (~won).any() else None, "p_fire_won": float(phi[won].mean()) if won.any() else None}


def _median(x):
    return float(np.median(x)) if len(x) else None


def score(cand, res, eps, tries, I, J, shown_tasks, shown_text, lam, max_steps):
    """cand = {"cid","spec","task","ref",...}; res = bit_rubric.simulate output -> the screen.json candidate record."""
    phi = np.zeros(len(eps)); fires, G, H, left, to_end, errs = [], 0.0, 0.0, [], [], 0
    for i, e in enumerate(eps):
        r = res.get(e["eid"]) or {"fires": [], "hook_errors": 0}; errs += int(r.get("hook_errors") or 0)
        if not r["fires"]: continue
        k = min(f["k"] for f in r["fires"]); phi[i] = 1
        d = next((j for j, s in enumerate(e["steps"]) if s["k"] == k), min(k, len(e["steps"])))   # trie depth = steps before the fire
        v = node_at(tries, e, d); st = beta_stats(len(v["won"]), len(v["lost"])); G += st["g"]; H += st["h"]
        left.append(max_steps - k); to_end.append(len(e["steps"]) - d)
        fires.append({"eid": e["eid"], "k": k, "won": e["won"], "node": v["id"], "g": round(st["g"], 4), "h": round(st["h"], 4)})
    won = [e["won"] for e in eps]; gw, ndisc, dr = pair_gain(phi, I, J, lam); ic, lo, hi = within_ic(phi, eps)
    # MATH v2: predictive leaf (Newton step on the within-task pairwise logistic loss at F=0: g=-1/2, h=1/4) -> rubric weight w_pred;
    # value_post = first-order gain with the node posterior V = 1 + g instead of the realized outcome (prop. 2)
    dd = np.asarray(phi, float)[np.asarray(I, int)] - np.asarray(phi, float)[np.asarray(J, int)] if len(I) else np.zeros(0)
    w_pred = float(-(-0.5 * dd.sum()) / (0.25 * (dd ** 2).sum() + lam))
    value_post = float(sum(-f["g"] * RHO - (1 + f["g"]) * C_HARM for f in fires))
    unshown = [i for i, e in enumerate(eps) if e["task"] not in shown_tasks]
    fired_tasks = {eps[i]["task"] for i in np.flatnonzero(phi)}
    hits = memo_hits(cand["spec"], shown_text) if not cand.get("ref") else []
    own_only = bool(cand.get("task")) and fired_tasks == {cand["task"]}
    sp = cand["spec"]
    return {"cid": cand["cid"], "ref": bool(cand.get("ref")), "run": cand.get("run"), "case_id": cand.get("case_id"), "task": cand.get("task"),
            "name": sp.get("name"), "kind": sp.get("kind"), "cls": sp.get("cls"), **_rates(phi, won),
            "n_lost_fired": int(sum(1 for f in fires if not f["won"])), "n_won_fired": int(sum(1 for f in fires if f["won"])),
            "ic": ic, "ic_lo90": lo, "ic_hi90": hi, "gain_within": gw if dr > 0 else 0.0, "gain_within_signed": gw, "n_discordant": ndisc,
            "dir": dr, "gain_raw": (G * G / (H + lam)) if fires else 0.0, "sum_g": G, "sum_h": H,
            # expected net recovered episodes (MATH §2 tau = s*a with a prior, §5 harm): rho per fired failure - c per fired success
            "w_pred": w_pred, "value_post": value_post,
            "value": RHO * sum(1 for f in fires if not f["won"]) - C_HARM * sum(1 for f in fires if f["won"]),
            "med_steps_left": _median(left), "med_steps_to_end": _median(to_end), "hook_errors": errs,
            "unshown": _rates(phi[unshown], [won[i] for i in unshown]),
            "memo": {"literals": hits, "own_task_only": own_only}, "memo_flag": bool(hits) or own_only,
            "fired_tasks": sorted(fired_tasks), "fires": fires, "dup_of": None, "error": None, "spec": sp}


RHO, C_HARM = 0.5, 0.2   # prior P(fixed | fired failure), prior P(broken | fired success); set by --rho / --harm


def jaccard(a, b):
    a, b = set(a), set(b); u = a | b
    return len(a & b) / len(u) if u else 0.0


def select(recs, k_within, k_raw, max_won_fire, jac):
    """dedupe (non-ref, scored candidates only) by Jaccard of fired eid sets, keeping the higher gain_within; then
    kept = top k_within by gain_within (> 0) + top k_raw by value (> 0) among P(fire|won) <= max_won_fire.
    (value replaces the plan's gain_raw for keeping: (sum g)^2/(sum h) grows with coverage, so an always-firing detector won.)"""
    pool = sorted([r for r in recs if not r["ref"] and r["error"] is None], key=lambda r: (-r["gain_within"], -r["gain_raw"], r["cid"]))
    uniq = []
    for r in pool:
        fs = [f["eid"] for f in r["fires"]]
        dup = next((u for u in uniq if jaccard(fs, [f["eid"] for f in u["fires"]]) >= jac), None)
        if dup is not None: r["dup_of"] = dup["cid"]
        else: uniq.append(r)
    kept = [r["cid"] for r in uniq if r["gain_within"] > 0][:k_within]
    raw = sorted([r for r in uniq if r["value"] > 0 and (r["p_fire_won"] or 0.0) <= max_won_fire and r["cid"] not in kept],
                 key=lambda r: (-r["value"], r["cid"]))
    kept += [r["cid"] for r in raw[:k_raw]]
    for r in recs: r["kept"] = r["cid"] in kept
    return kept


def rank_raw(recs, max_won_fire):
    """raw_eligible = P(fire|won) <= max_won_fire (the gain_raw keep filter); raw_rank = 1-based gain_raw rank among eligible scored
    candidates, refs included (unfiltered gain_raw grows with coverage: an always-firing detector covers all failure mass)."""
    ok = [r for r in recs if r["error"] is None and r["n_fire"] > 0 and (r["p_fire_won"] or 0.0) <= max_won_fire]; ids = {id(r) for r in ok}
    for r in recs: r["raw_eligible"], r["raw_rank"] = id(r) in ids, None
    for i, r in enumerate(sorted(ok, key=lambda r: (-r["value"], r["cid"])), 1): r["raw_rank"] = i


def load_cands(paths, refs):
    cands, skipped = [], collections.Counter()
    for p in [x for x in paths.split(",") if x]:
        for ln, line in enumerate(open(p, encoding="utf-8"), 1):
            if not line.strip(): continue
            try: c = json.loads(line)
            except json.JSONDecodeError: skipped["bad_json"] += 1; continue
            if not c.get("valid") or not isinstance(c.get("spec"), dict): skipped["invalid"] += 1; continue
            org = c["spec"].get("origin") or {}
            cands.append({"cid": c.get("cid") or f"{os.path.basename(p)}:{ln}", "run": c.get("run") or org.get("run"),
                          "case_id": c.get("case_id") or org.get("case_id"), "task": c.get("task"), "spec": c["spec"],
                          "patch_path": c.get("patch_path"), "ref": False})
    for p in [x for x in refs.split(",") if x]:
        sp = json.load(open(p, encoding="utf-8"))
        cands.append({"cid": "ref_" + sp.get("name", os.path.basename(p)), "run": "ref", "case_id": None, "task": None, "spec": sp,
                      "patch_path": p, "ref": True})
    seen = collections.Counter(c["cid"] for c in cands)
    if any(v > 1 for v in seen.values()): raise SystemExit(f"duplicate cids: {[k for k, v in seen.items() if v > 1]}")
    return cands, dict(skipped)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", default="", help="comma list of cands JSONL files (bit_propose.py)")
    ap.add_argument("--refs", default="", help="comma list of reference spec JSONs (scored, marked ref, never kept)")
    ap.add_argument("--runs", required=True, help="comma list of base discovery run logs")
    ap.add_argument("--instr", required=True); ap.add_argument("--tree", required=True, help="bit_tree.py tree.json (shown cases)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--k-within", type=int, default=4); ap.add_argument("--k-raw", type=int, default=4)
    ap.add_argument("--max-won-fire", type=float, default=0.05); ap.add_argument("--lam", type=float, default=1.0)
    ap.add_argument("--rho", type=float, default=0.5); ap.add_argument("--harm", type=float, default=0.2)
    ap.add_argument("--jaccard", type=float, default=0.8)
    ap.add_argument("--max-steps", type=int, default=None, help="default 30 (AppWorld) / the runs' max_steps (Gaia2)")
    ap.add_argument("--workers", type=int, default=min(6, os.cpu_count() or 1)); ap.add_argument("--timeout", type=float, default=120)
    a = ap.parse_args(); global RHO, C_HARM; RHO, C_HARM = a.rho, a.harm
    import bit_rubric as R
    t0 = time.time(); instr = json.load(open(a.instr, encoding="utf-8"))
    all_eps = load_episodes(a.runs, instr); byeid = {e["eid"]: e for e in all_eps}
    eps = [e for e in all_eps if not e["crashed"] and not e["has_replay"]]
    if a.max_steps is None:
        a.max_steps = max((e.get("max_steps") or 40 for e in eps), default=40) if any(e.get("bench") == "gaia2" for e in eps) else 30
    slim = [{**e, "steps": [{k: v for k, v in s.items() if k != "resp"} for s in e["steps"]]} for e in eps]   # simulate never reads resp
    tries = build_tries(eps); I, J, _ = make_pairs(eps)
    tree = json.load(open(a.tree, encoding="utf-8")); case_task = {c["case_id"]: c["task"] for c in tree["cases"]}
    cands, skipped = load_cands(a.cands, a.refs)
    for c in cands:
        if not c["task"] and c["case_id"] in case_task: c["task"] = case_task[c["case_id"]]
    shown_tasks = {c["task"] for c in tree["cases"]} | {c["task"] for c in cands if c["task"] and not c["ref"]}
    shown_eids = {x for c in tree["cases"] for x in (c["lost"], c["won"]) if x}
    ep_instr = {e["task"]: e["instr"] for e in all_eps}   # = instr[t], or the run's own instr list (Gaia2)
    parts = [instr.get(t) or ep_instr.get(t, "") for t in sorted(shown_tasks)]
    for x in sorted(shown_eids):
        if x in byeid: parts += [s["code"] + "\n" + s["out"] for s in byeid[x]["steps"]]
    shown_text = _norm("\n".join(parts))

    def run(c):
        try:
            src = R.compile_patch([c["spec"]], a.max_steps)
            return c, R.simulate(src, slim, stop_at_first=True, timeout_s=a.timeout), None
        except Exception as e:   # SimulationError (timeout / crash), ValueError (spec no longer validates), ...
            return c, None, f"{type(e).__name__}: {str(e)[:300]}"

    recs = []
    with ThreadPoolExecutor(max(1, a.workers)) as ex:
        for c, res, err in ex.map(run, cands):
            if err is not None:
                sp = c["spec"]
                recs.append({"cid": c["cid"], "ref": c["ref"], "run": c.get("run"), "case_id": c.get("case_id"), "task": c.get("task"),
                             "name": sp.get("name"), "kind": sp.get("kind"), "cls": sp.get("cls"), "error": err, "kept": False, "spec": sp})
                continue
            recs.append(score(c, res, eps, tries, I, J, shown_tasks, shown_text, a.lam, a.max_steps))
    kept = select(recs, a.k_within, a.k_raw, a.max_won_fire, a.jaccard); rank_raw(recs, a.max_won_fire)
    params = {"runs": a.runs.split(","), "cands": [x for x in a.cands.split(",") if x], "refs": [x for x in a.refs.split(",") if x],
              "tree": a.tree, "n_episodes": len(eps), "n_won": int(sum(e["won"] for e in eps)), "n_pairs": int(len(I)),
              "n_excluded_crashed_or_replay": len(all_eps) - len(eps), "skipped_lines": skipped,
              "k_within": a.k_within, "k_raw": a.k_raw, "max_won_fire": a.max_won_fire, "lam": a.lam, "jaccard": a.jaccard,
              "max_steps": a.max_steps, "shown_tasks": sorted(shown_tasks), "n_errors": sum(1 for r in recs if r["error"]),
              "seconds": round(time.time() - t0, 1)}
    if os.path.dirname(a.out): os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({"params": params, "candidates": recs, "kept": kept}, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"{len(eps)} episodes ({params['n_won']} won), {len(I)} same-task pairs, {len(recs)} candidates "
          f"({params['n_errors']} errors, skipped {skipped}) in {params['seconds']}s -> {a.out}")
    print(f"  {'cid':34s} {'kind':10s} fire  P|L   P|W    ic [lo90,hi90]       dir g_within g_raw rk left memo")
    for r in sorted(recs, key=lambda r: (r["error"] is not None, r.get("raw_rank") is None, r.get("raw_rank") or 0, -(r.get("gain_raw") or 0))):
        if r["error"]: print(f"  {r['cid']:34s} ERROR {r['error'][:100]}"); continue
        f = lambda x: "  -  " if x is None else f"{x:.2f}"
        print(f"  {r['cid'][:34]:34s} {r['kind']:10s} {r['n_fire']:4d} {f(r['p_fire_lost'])} {f(r['p_fire_won'])} {r['ic']:+.2f} "
              f"[{r['ic_lo90']:+.2f},{r['ic_hi90']:+.2f}] {r['dir']:+d} {r['gain_within']:7.3f} {r['gain_raw']:6.2f} {r['raw_rank'] or '-':>2} "
              f"{r['med_steps_left'] if r['med_steps_left'] is not None else '-':>4} {'M' if r['memo_flag'] else ''}"
              f"{' REF' if r['ref'] else ''}{' KEPT' if r['kept'] else ''}{' dup:' + r['dup_of'] if r['dup_of'] else ''}")


if __name__ == "__main__":
    main()
