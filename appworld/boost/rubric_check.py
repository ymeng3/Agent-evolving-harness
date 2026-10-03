"""Step 2 of the diagnosis track (prereg A7): rubric dimensions designed from the diagnosed error classes
(docs/design/diagnosis_2026-10-03/TAXONOMY.md), implemented as ONLINE code detectors (they only use what the harness sees while the
episode runs), and checked on logs: does each fire more on failures than on successes, within the same task, and does that hold on
validation (new task families)? usage: python boost/rubric_check.py --disc A.json,B.json,... --val C.json,D.json,..."""
import argparse, collections, json, re
import numpy as np

API = re.compile(r"apis\.([a-z_]+)\.([a-z_]+)\s*\(")
LIT = re.compile(r"""("([^"\\]|\\.)*"|'([^'\\]|\\.)*'|\b\d+(\.\d+)?\b)""")


def norm(code): return " ".join(LIT.sub("§", code).split())


def is_docs(c): return "api_docs" in c


def detectors(tr):
    """-> dict name -> (fired: bool, first_cell or None). tr = logged steps of one episode."""
    cells = [(s.get("code") or "", s.get("out") or "", s) for s in tr]; d = {}
    def first(pred):
        for k in range(len(cells)):
            if pred(k): return k
        return None
    # D1 docs-heavy pacing: >= 50% of the first 10 cells are api_docs calls (fires at cell 9 at the earliest)
    d["D1_docs_heavy"] = first(lambda k: k == 9 and sum(is_docs(c[0]) for c in cells[:10]) >= 5)
    # D2 per-item cells: two consecutive cells with identical code up to literals, different raw code, calling a non-docs API
    d["D2_per_item"] = first(lambda k: k > 0 and cells[k][0] != cells[k - 1][0] and norm(cells[k][0]) == norm(cells[k - 1][0])
                             and any(a != "api_docs" for a, _ in API.findall(cells[k][0])))
    # D3 harness artifact: default fallback, syntax error from cut-off code, or a '...' placeholder executed
    d["D3_artifact"] = first(lambda k: cells[k][2].get("default_code") or "SyntaxError" in cells[k][1] or re.search(r"\(\s*\.\.\.\s*\)|=\s*\.\.\.", cells[k][0]))
    # D4 API misuse: unexpected parameter / unknown API / attribute errors from the environment
    d["D4_api_misuse"] = first(lambda k: re.search(r"Unexpected parameter|unexpected keyword|No API named|has no attribute|not a valid API", cells[k][1], re.I))
    # D5 no-code streak (ambiguity paralysis): >= 2 consecutive default-fallback (code-less) turns
    d["D5_no_code_streak"] = first(lambda k: k > 0 and cells[k][2].get("default_code") and cells[k - 1][2].get("default_code"))
    # D6 wrong data source: supervisor addresses / payment cards fetched in an episode that uses amazon
    uses_amazon = any("apis.amazon." in c[0] for c in cells)
    d["D6_supervisor_detour"] = first(lambda k: uses_amazon and re.search(r"apis\.supervisor\.(show_addresses|show_payment_cards)\s*\(", cells[k][0]))
    # D8 repeated identical docs call (truncated listing re-printed, or spec re-read)
    seen = collections.Counter()
    def rep(k):
        if not is_docs(cells[k][0]): return False
        key = " ".join(cells[k][0].split()); seen[key] += 1; return seen[key] == 2
    d["D8_docs_repeat"] = first(rep)
    # D9 search re-query: the same search/list API called 3+ times in the episode with different arguments
    cnt = collections.Counter(); args = collections.defaultdict(set)
    def requery(k):
        for a, f in API.findall(cells[k][0]):
            if a != "api_docs" and (f.startswith("search") or f.startswith("show_inbox") or f.startswith("show_outbox")):
                args[(a, f)].add(cells[k][0]);
                if len(args[(a, f)]) == 3: return True
        return False
    d["D9_search_requery"] = first(requery)
    # D7 end-of-budget waste (diagnostic only, not online-predictive): 30 cells, no complete_task call, and a docs / read call in the last 3
    done = any(re.search(r"apis\.supervisor\.complete_task\s*\(", c[0]) for c in cells)
    d["D7_endgame_waste"] = (len(cells) - 1) if (len(cells) >= 30 and not done and any(is_docs(c[0]) or ".show_" in c[0] for c in cells[-3:])) else None
    return {k: (v is not None, v) for k, v in d.items()}


def load(paths):
    rows = []
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        for t, w, tr, cr in zip(d["games"], d["won"], d["traj"], d.get("crashed") or [None] * len(d["games"])):
            if cr: continue
            rows.append({"task": t, "won": bool(w), "det": detectors(tr), "run": d["tag"] + str(d["seed"])})
    return rows


def boot_ci(groups, fn, B=2000, seed=0):
    u = sorted(set(groups)); rng = np.random.default_rng(seed); st = []
    for _ in range(B):
        pick = [u[j] for j in rng.choice(len(u), len(u), replace=True)]; v = fn(pick)
        if v is not None and np.isfinite(v): st.append(v)
    return (float(np.quantile(st, 0.05)), float(np.quantile(st, 0.95))) if st else (float("nan"), float("nan"))


def report(rows, label):
    names = sorted(rows[0]["det"]); by_task = collections.defaultdict(list)
    for r in rows: by_task[r["task"]].append(r)
    mixed = [t for t, rs in by_task.items() if 0 < sum(r["won"] for r in rs) < len(rs)]
    print(f"\n== {label}: {len(rows)} episodes, {len(by_task)} tasks, win rate {np.mean([r['won'] for r in rows]):.2f}, mixed tasks {len(mixed)}")
    print(f"{'detector':22s} {'P(fire|lost)':>12s} {'P(fire|won)':>11s} {'diff [90% CI]':>24s}   {'within-task diff [90% CI] (mixed tasks)':>40s}  {'win|fire':>8s} {'win|no':>7s}")
    out = {}
    for n in names:
        def diff(tasks):
            rs = [r for t in tasks for r in by_task[t]]; L = [r["det"][n][0] for r in rs if not r["won"]]; W = [r["det"][n][0] for r in rs if r["won"]]
            return (np.mean(L) - np.mean(W)) if L and W else None
        def wdiff(tasks):
            v = []
            for t in tasks:
                rs = by_task[t]; L = [r["det"][n][0] for r in rs if not r["won"]]; W = [r["det"][n][0] for r in rs if r["won"]]
                if L and W: v.append(np.mean(L) - np.mean(W))
            return np.mean(v) if v else None
        all_t = list(by_task); dv = diff(all_t); lo, hi = boot_ci(all_t, diff); wv = wdiff(mixed); wlo, whi = boot_ci(mixed, wdiff) if mixed else (np.nan, np.nan)
        pl = np.mean([r["det"][n][0] for r in rows if not r["won"]]); pw = np.mean([r["det"][n][0] for r in rows if r["won"]])
        f = [r["won"] for r in rows if r["det"][n][0]]; nf = [r["won"] for r in rows if not r["det"][n][0]]
        print(f"{n:22s} {pl:12.2f} {pw:11.2f} {dv:+8.2f} [{lo:+.2f}, {hi:+.2f}]   {(wv if wv is not None else float('nan')):+18.2f} [{wlo:+.2f}, {whi:+.2f}]         "
              f"{(np.mean(f) if f else float('nan')):8.2f} {(np.mean(nf) if nf else float('nan')):7.2f}  (n_fire={len(f)})")
        out[n] = {"p_lost": pl, "p_won": pw, "diff": dv, "ci": [lo, hi], "within": wv, "within_ci": [wlo, whi], "n_fire": len(f)}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--disc", required=True); ap.add_argument("--val", required=True); ap.add_argument("--out"); a = ap.parse_args()
    res = {"discovery": report(load(a.disc.split(",")), "DISCOVERY"), "validation": report(load(a.val.split(",")), "VALIDATION")}
    if a.out: json.dump(res, open(a.out, "w"), indent=1)
