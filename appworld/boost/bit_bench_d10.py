"""BIT Unit G (docs/design/BIT_IMPLEMENTATION_PLAN.md): D10 rediscovery benchmark on the H1 discovery base.
Gold set (frozen before any proposer run): lost episodes of CC_H1_F0_disc_seed{1,2} whose final executed cell calls
apis.supervisor.complete_task with a non-None answer, on a task with no question cue (the R3_H2 cue rule verbatim), and whose final
step k < max_steps-1 (block_once never fires at the last step). Built by a small ast-based parser that is independent of D10_ref's
detect, and cross-checked against simulate(compile_patch([D10_ref])).
A candidate REDISCOVERS D10 iff on all H1 disc episodes: recall >= 0.6, precision >= 0.5, <= 2 won episodes fired, where a gold
episode counts as hit only if the fire step is the final complete_task step (block_once) or 0..2 steps before it (note).
  recall = hits / |gold|;  precision = hits / #episodes fired (any step, won or lost).
usage: python boost/bit_bench_d10.py gold  [--runs A,B --instr I] [--out boost/bit_refs/d10_gold_H1disc.json]
       python boost/bit_bench_d10.py bench --cands cands_P1.jsonl[,cands_P2.jsonl] [--screen screen.json] [--tree tree.json]
                                           [--runs A,B --instr I --gold G] [--out bench.json] [--workers 6]
--runs/--instr default to the H1 disc logs in $BIT_CCD (the local data dir)."""
import argparse, ast, collections, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)

CCD = os.environ.get("BIT_CCD") or (r"C:\Users\Owner\AppData\Local\Temp\claude\C--Projects-Cleanup-Archives-2026-08-27-Local-Latex-Files-"
                                    r"Local-Latex-Files-Agent-evolving-harness\57e9c937-6acb-4624-9f6e-81989b534107\scratchpad\ccdata")
DEF_RUNS = ",".join(os.path.join(CCD, f"CC_H1_F0_disc_seed{s}.json") for s in (1, 2))
DEF_INSTR = os.path.join(CCD, "instructions_all100.json")
REFS = os.path.join(HERE, "bit_refs"); DEF_GOLD = os.path.join(REFS, "d10_gold_H1disc.json")
RECALL, PRECISION, MAX_WON, NOTE_LEAD = 0.6, 0.5, 2, 2


# ---------------------------------------------------------------- gold set (independent parser)
def question_cue(task):
    """patches_ccdiag/R3_H2.py e1_pre_complete cue rule, verbatim."""
    task = re.sub(r'"[^"]*"|“[^”]*”|(?<![A-Za-z])\'[^\']{1,200}\'(?![A-Za-z])', " ", task or "")
    return bool(re.search(r"\?|\b(tell me|let me know|give me|find out|how many|how much|how long|what is|what are|what was|what's|which one)\b", task, re.I)
                or re.match(r"\s*(what|which|who|whom|when|where|how|is|are|do|does|did|can|could|should|was|were)\b", task, re.I))


def ct_answers(code):
    """answers passed to apis.supervisor.complete_task in a cell: list of 'None' / source text of the answer / '' (no answer).
    ast-based; a cell that does not parse falls back to a regex on the first argument."""
    try: tree = ast.parse(code)
    except SyntaxError:
        return [("" if m.group(2) == ")" else ("None" if re.match(r"None\s*\)", code[m.start(2):]) else "?"))
                for m in re.finditer(r"apis\.supervisor\.complete_task\s*\(\s*(answer\s*=\s*)?(\S)", code)]
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and ast.unparse(n.func).replace(" ", "") == "apis.supervisor.complete_task":
            a = next((k.value for k in n.keywords if k.arg == "answer"), n.args[0] if n.args else None)
            out.append("" if a is None else ("None" if isinstance(a, ast.Constant) and a.value is None else ast.unparse(a)))
    return out


def build_gold(runs, instr):
    """-> gold dict (see main); parses the raw run JSONs (not bit_common) so it shares no code with the simulator path."""
    if isinstance(instr, str): instr = json.load(open(instr, encoding="utf-8"))
    gold, final_k, excluded, rows = [], {}, [], []
    for p in runs:
        d = json.load(open(p, encoding="utf-8")); ms = int(d.get("max_steps") or 30); crashed = d.get("crashed") or [None] * len(d["games"])
        for t, w, tr, cr in zip(d["games"], d["won"], d["traj"], crashed):
            if w or cr: continue
            ex = [s for s in tr or [] if (s.get("code") or "").strip() and not s.get("no_exec") and not s.get("replayed")]
            if not ex: continue
            last = ex[-1]; ans = ct_answers(last["code"]); eid = f"{d['tag']}_s{d['seed']}:{t}"
            non_none = [a for a in ans if a not in ("", "None")]; cue = question_cue(instr.get(t, ""))
            if not non_none or cue: continue
            rows.append({"eid": eid, "k_final": last["step"], "answer": non_none[0][:80], "max_steps": ms})
            if last["step"] < ms - 1: gold.append(eid); final_k[eid] = last["step"]
            else: excluded.append(eid)
    return {"gold": gold, "final_k": final_k, "excluded_last_step": excluded, "candidates": rows}


def d10_fires(eps, timeout_s=300):
    import bit_rubric as BR
    ref = json.load(open(os.path.join(REFS, "D10_ref.json"), encoding="utf-8"))
    res = BR.simulate(BR.compile_patch([ref]), eps, timeout_s=timeout_s)
    return {e: r["fires"][0]["k"] for e, r in res.items() if r["fires"]}


def cmd_gold(a):
    import bit_common
    runs = [p for p in a.runs.split(",") if p]; instr = json.load(open(a.instr, encoding="utf-8"))
    g = build_gold(runs, instr)
    eps = [e for e in bit_common.load_episodes(runs, instr) if not e["crashed"]]
    fires = d10_fires(eps); byid = {e["eid"]: e for e in eps}
    sim_lost = sorted(e for e in fires if not byid[e]["won"]); sim_won = sorted(e for e in fires if byid[e]["won"])
    agree = set(sim_lost) == set(g["gold"]) and all(fires[e] == g["final_k"][e] for e in g["gold"]) and not sim_won
    seeds = collections.OrderedDict()
    for e in g["gold"]: seeds.setdefault(e.split(":")[0], []).append(e.split(":")[1])
    out = {"note": "D10 rediscovery gold set, frozen before any proposer run (BIT_IMPLEMENTATION_PLAN Unit G + 'Integration decisions after "
                   "Wave 1'). Built by bit_bench_d10.py gold: lost, non-crashed episodes whose final executed cell (last non-empty, non-no_exec "
                   "step) calls apis.supervisor.complete_task with a non-None answer (ast parse of the logged executed code), on a task with "
                   "no question cue (patches_ccdiag/R3_H2.py rule verbatim, on instructions_all100.json), and whose final step "
                   "k < max_steps-1 (block_once never fires at the last step). Cross-checked against simulate(compile_patch([D10_ref])).",
           "runs": [os.path.basename(p) for p in runs], "rule": {"recall": RECALL, "precision": PRECISION, "max_won_fired": MAX_WON,
                                                                 "note_lead_steps": NOTE_LEAD},
           "gold": g["gold"], "final_k": g["final_k"], "per_run": seeds, "excluded_last_step": g["excluded_last_step"],
           "parser_rows": g["candidates"],
           "cross_check": {"d10_ref_fired_lost": sim_lost, "d10_ref_fired_won": sim_won, "fire_k": {e: fires[e] for e in sim_lost}, "agree": agree}}
    for run, tids in seeds.items(): print(f"{run}: {len(tids)} gold  {' '.join(tids)}")
    print(f"excluded (final complete_task at the last step): {' '.join(g['excluded_last_step']) or '-'}")
    print(f"cross-check D10_ref simulate: lost fired {len(sim_lost)}, won fired {len(sim_won)}, agree={agree}")
    if not agree:
        print("  parser only:", sorted(set(g["gold"]) - set(sim_lost)), " simulate only:", sorted(set(sim_lost) - set(g["gold"])))
    if a.out:
        json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False); print("->", a.out)
    return out


# ---------------------------------------------------------------- rediscovery check
def check(spec, fired, eps, gold):
    """fired: {episode eid: first fire step k}. -> metrics + pass flag."""
    byid = {e["eid"]: e for e in eps}; G = set(gold["gold"]); fk = gold["final_k"]
    def on_time(e, k): return k == fk[e] if spec["kind"] == "block_once" else fk[e] - NOTE_LEAD <= k <= fk[e]
    hits = sorted(e for e, k in fired.items() if e in G and on_time(e, k))
    n_fired = len(fired); won = sorted(e for e in fired if byid[e]["won"])
    rec = len(hits) / len(G) if G else 0.0; prec = len(hits) / n_fired if n_fired else 0.0
    return {"recall": rec, "precision": prec, "n_hits": len(hits), "n_gold_fired_any_step": len(set(fired) & G), "n_fired": n_fired,
            "n_won_fired": len(won), "n_lost_fired": n_fired - len(won), "hits": hits, "won_fired": won,
            "passes": rec >= RECALL and prec >= PRECISION and len(won) <= MAX_WON}


def run_spec(spec, eps, gold, timeout_s=300):
    import bit_rubric as BR
    try: res = BR.simulate(BR.compile_patch([spec]), eps, timeout_s=timeout_s)
    except Exception as e: return {"error": f"{type(e).__name__}: {str(e)[:300]}", "passes": False}
    fired = {e: r["fires"][0]["k"] for e, r in res.items() if r["fires"]}
    return {**check(spec, fired, eps, gold), "fired": fired, "hook_errors": sum(r["hook_errors"] for r in res.values())}


def fallback_gains(fired, eps):
    """screen.json absent: gain_within = pair_gain on same-task (won, lost) pairs (0 if direction <= 0); gain_raw = (sum_fired g)^2 /
    (sum_fired h + 1) with g, h of the trie node at the fire depth. Base episodes = not crashed, no replayed steps (as Unit E)."""
    import bit_common as BC, bit_tree as BT
    base = [e for e in eps if not e["crashed"] and not e["has_replay"]]; phi = [1.0 if e["eid"] in fired else 0.0 for e in base]
    I, J, _ = BC.make_pairs(base); gw, _, dr = BC.pair_gain(phi, I, J); tries = BT.build_tries(base); sg = sh = 0.0
    for e in base:
        if e["eid"] not in fired: continue
        depth = next((i for i, s in enumerate(e["steps"]) if s["k"] == fired[e["eid"]]), len(e["steps"]))
        v = BT.node_at(tries, e, depth); st = BC.beta_stats(len(v["won"]), len(v["lost"])); sg += st["g"]; sh += st["h"]
    won = {e["eid"]: e["won"] for e in base}; nl = sum(1 for e in fired if e in won and not won[e]); nw = sum(1 for e in fired if won.get(e))
    return {"gain_within": gw if dr > 0 else 0.0, "gain_raw": sg * sg / (sh + 1.0), "value": 0.5 * nl - 0.2 * nw, "gains_from": "fallback"}


def shown_lost(lines, tree):
    """lost eids of the cases the proposer was shown (every case with a line, valid or not)."""
    cases = {l.get("case_id") for l in lines if l.get("case_id")}
    if tree is None: return None, sorted(cases)
    m = {c["case_id"]: c["lost"] for c in tree.get("cases", [])}
    return sorted({m[c] for c in cases if c in m}), sorted(cases)


def bench(cand_paths, eps, gold, screen=None, tree=None, workers=6, timeout_s=300):
    lines = []
    for p in cand_paths:
        for ln in open(p, encoding="utf-8"):
            if ln.strip(): lines.append(json.loads(ln))
    sc = {c.get("cid"): c for c in (screen or {}).get("candidates", []) if c.get("cid")}; kept = set((screen or {}).get("kept", []))
    valid = [l for l in lines if l.get("valid") and l.get("spec")]
    with ThreadPoolExecutor(max(1, workers)) as ex:   # each simulate() spawns its own process
        res = dict(zip([l["cid"] for l in valid], ex.map(lambda l: run_spec(l["spec"], eps, gold, timeout_s), valid)))
    for l in valid:
        r = res[l["cid"]]; s = sc.get(l["cid"])
        r.update({"gain_within": s.get("gain_within"), "gain_raw": s.get("gain_raw"), "value": s.get("value"), "gains_from": "screen"} if s else
                 (fallback_gains(r["fired"], eps) if "fired" in r else {"gain_within": None, "gain_raw": None, "gains_from": None}))
    report = {"rule": {"recall": RECALL, "precision": PRECISION, "max_won_fired": MAX_WON, "note_lead_steps": NOTE_LEAD},
              "n_gold": len(gold["gold"]), "n_episodes": len(eps), "runs": {}}
    by_run = collections.OrderedDict()
    for l in lines: by_run.setdefault(l.get("run") or ((l.get("spec") or {}).get("origin") or {}).get("run") or "?", []).append(l)
    G = set(gold["gold"])
    for run, ls in by_run.items():
        lost, cases = shown_lost(ls, tree)
        exposure = None if lost is None else len([e for e in lost if e in G])
        vs = [l for l in ls if l.get("valid") and l.get("spec")]
        def passes(cands): return any(res[l["cid"]]["passes"] for l in cands)
        def top1(key):
            c = [l for l in vs if res[l["cid"]].get(key) is not None]
            if not c: return None
            b = max(c, key=lambda l: res[l["cid"]][key]); return {"cid": b["cid"], key: res[b["cid"]][key], "passes": res[b["cid"]]["passes"]}
        kept_ls = [l for l in vs if l["cid"] in kept]
        best = max(vs, key=lambda l: (res[l["cid"]]["passes"], res[l["cid"]].get("n_hits", 0), res[l["cid"]].get("precision", 0.0),
                                      -res[l["cid"]].get("n_won_fired", 99)), default=None)
        t_w, t_r = top1("gain_within"), top1("value")   # top-1 by expected net value (gain_raw grows with coverage)
        report["runs"][run] = {
            "n_lines": len(ls), "n_valid": len(vs), "n_cases_shown": len(cases),
            "exposure": exposure, "exposure_note": ("no tree.json given: shown-case -> lost-eid map unknown" if exposure is None else
                                                    "not testable (no gold case shown)" if exposure == 0 else "testable"),
            "shown_gold": None if lost is None else sorted(e for e in lost if e in G),
            "rediscovery": {"any_valid": passes(vs), "screen_kept": passes(kept_ls) if screen else None, "n_kept": len(kept_ls) if screen else None,
                            "top1_gain_within": t_w, "top1_gain_raw": t_r},
            "best": None if best is None else {"cid": best["cid"], "name": best["spec"].get("name"), "kind": best["spec"].get("kind"),
                                                "cls": best["spec"].get("cls"), **{k: res[best["cid"]].get(k) for k in
                                                ("passes", "recall", "precision", "n_hits", "n_fired", "n_won_fired", "hits", "error")}},
            "candidates": {l["cid"]: {"name": l["spec"].get("name"), "kind": l["spec"].get("kind"), "cls": l["spec"].get("cls"),
                                      **{k: v for k, v in res[l["cid"]].items() if k != "fired"}} for l in vs}}
    return report


def sanity(eps, gold):
    """D10_ref must pass the rediscovery check; null_note must fail."""
    out = {}
    for name in ("D10_ref", "null_note"):
        spec = json.load(open(os.path.join(REFS, f"{name}.json"), encoding="utf-8")); r = run_spec(spec, eps, gold)
        out[name] = {k: r.get(k) for k in ("passes", "recall", "precision", "n_hits", "n_fired", "n_won_fired", "error")}
    out["ok"] = bool(out["D10_ref"]["passes"]) and not out["null_note"]["passes"]
    return out


def cmd_bench(a):
    import bit_common
    gold = json.load(open(a.gold, encoding="utf-8"))
    eps = [{**e, "steps": [{k: v for k, v in s.items() if k != "resp"} for s in e["steps"]]}   # simulate never reads resp
           for e in bit_common.load_episodes(a.runs, a.instr) if not e["crashed"]]
    miss = [e for e in gold["gold"] if e not in {x["eid"] for x in eps}]
    if miss: sys.exit(f"gold episodes missing from --runs: {miss}")
    san = None if a.no_sanity else sanity(eps, gold)
    if san is not None:
        print("sanity:", json.dumps(san))
        if not san["ok"]: print("WARNING: sanity failed (D10_ref must pass, null_note must fail)")
    screen = json.load(open(a.screen, encoding="utf-8")) if a.screen else None
    tree = json.load(open(a.tree, encoding="utf-8")) if a.tree else None
    rep = bench([p for p in a.cands.split(",") if p], eps, gold, screen, tree, a.workers, a.timeout)
    rep["sanity"] = san
    for run, r in rep["runs"].items():
        rd = r["rediscovery"]; b = r["best"] or {}
        tw = rd["top1_gain_within"] or {}; tr = rd["top1_gain_raw"] or {}
        print(f"[{run}] valid {r['n_valid']}/{r['n_lines']}  cases shown {r['n_cases_shown']}  exposure {r['exposure']} ({r['exposure_note']})")
        print(f"   rediscovery: any={rd['any_valid']}  kept={rd['screen_kept']} (n_kept={rd['n_kept']})  "
              f"top1_within={tw.get('passes')} ({tw.get('cid')})  top1_raw={tr.get('passes')} ({tr.get('cid')})")
        if b: print(f"   best {b['cid']} [{b['kind']}/{b['cls']}] recall {b['recall']} precision {b['precision']} won_fired {b['n_won_fired']}")
    if a.out:
        json.dump(rep, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False); print("->", a.out)
    return rep


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["gold", "bench"])
    ap.add_argument("--runs", default=DEF_RUNS); ap.add_argument("--instr", default=DEF_INSTR); ap.add_argument("--out")
    ap.add_argument("--gold", default=DEF_GOLD); ap.add_argument("--cands"); ap.add_argument("--screen"); ap.add_argument("--tree")
    ap.add_argument("--workers", type=int, default=6); ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--no-sanity", action="store_true"); a = ap.parse_args()
    if a.cmd == "gold": cmd_gold(a)
    else:
        if not a.cands: ap.error("bench needs --cands")
        cmd_bench(a)


if __name__ == "__main__":
    main()
