"""BIT common helpers (docs/design/BIT_IMPLEMENTATION_PLAN.md, Unit A): episode loading, same-task (winner, loser) pairs, the pairwise
split gain at margin 0, the within-task IC with a task bootstrap, Beta node statistics, and the sign-flip / bootstrap helpers.
Episode: {"eid": f"{tag}_s{seed}:{tid}", "task", "tag", "seed", "won", "G", "instr", "harness_h1", "crashed", "has_replay",
          "bench", "max_steps", "steps": [{"k", "code", "out", "err", "no_exec", "replayed", "resp"}]}   (code = executed code, out <= 200
          chars as logged; bench = the run's "bench" ("appworld" if absent); Gaia2 episodes also carry the per-episode G2_KEYS)"""
import collections, itertools, json
import numpy as np

G2_KEYS = ("end_reason", "nb_turns", "turns_done", "rationale", "rationale_diag")   # per-episode lists of a Gaia2 run (GAIA2_ADAPTER_PLAN 2)


def load_episodes(paths, instr):
    """paths: list (or comma string) of run JSONs; instr: {tid: instruction} or a path to such a JSON. Crashed episodes are kept
    (crashed=True) so callers decide; goal-check fields other than G are dropped. A tid missing from instr falls back to the run's own
    per-episode "instr" list (Gaia2 runs log it)."""
    if isinstance(paths, str): paths = [p for p in paths.split(",") if p]
    if isinstance(instr, str): instr = json.load(open(instr, encoding="utf-8")) if instr else {}
    instr = instr or {}; eps = []
    for p in paths:
        d = json.load(open(p, encoding="utf-8")); n = len(d["games"])
        crashed = d.get("crashed") or [None] * n; Gs = d.get("G") or [None] * n
        bench = d.get("bench", "appworld"); own = d.get("instr") if isinstance(d.get("instr"), list) else [None] * n
        for i, (t, w, tr, cr, G) in enumerate(zip(d["games"], d["won"], d["traj"], crashed, Gs)):
            steps = []
            for s in tr or []:
                code = s.get("code") or ""; out = s.get("out") or ""; rep = bool(s.get("replayed"))
                steps.append({"k": s["step"], "code": code, "out": out, "err": out.startswith("Execution failed"),
                              "no_exec": bool(s.get("no_exec")) or (not code and not rep), "replayed": rep, "resp": s.get("resp") or ""})
            ep = {"eid": f"{d['tag']}_s{d['seed']}:{t}", "task": t, "tag": d["tag"], "seed": d["seed"], "won": bool(w), "G": G,
                  "instr": instr.get(t) or (own[i] if i < len(own) else None) or "", "harness_h1": bool(d.get("harness_h1")), "crashed": bool(cr),
                  "has_replay": any(s["replayed"] for s in steps), "bench": bench, "max_steps": d.get("max_steps"), "steps": steps}
            if bench == "gaia2":
                for k in G2_KEYS:
                    v = d.get(k); ep[k] = v[i] if isinstance(v, list) and i < len(v) else None
            eps.append(ep)
    return eps


def make_pairs(eps):
    """-> (I, J, task_of_pair): every same-task (winner, loser) combination (copy of loop_pw.make_pairs)."""
    by = collections.defaultdict(list)
    for i, r in enumerate(eps): by[r["task"]].append(i)
    I, J, T = [], [], []
    for t, ix in by.items():
        for a, b in itertools.combinations(ix, 2):
            if eps[a]["won"] == eps[b]["won"]: continue
            w, l = (a, b) if eps[a]["won"] else (b, a); I.append(w); J.append(l); T.append(t)
    return np.array(I, int), np.array(J, int), T


def pair_gain(phi, I, J, lam=1.0):
    """pairwise split gain of indicator/feature phi at margin 0 (g = sigma(0) - 1 = -0.5, h = 0.25) -> (gain, n_discordant, direction);
    direction = sign(sum(phi[J] - phi[I])): +1 = fires more on the losers of same-task pairs."""
    phi = np.asarray(phi, float); I = np.asarray(I, int); J = np.asarray(J, int)
    if len(I) == 0: return 0.0, 0, 0
    d = phi[I] - phi[J]; g, h = -0.5, 0.25
    gain = float((g * d).sum() ** 2 / (2 * ((h * d ** 2).sum() + lam)))
    return gain, int((d != 0).sum()), int(np.sign((phi[J] - phi[I]).sum()))


def within_ic(phi, eps, B=2000, seed=0):
    """mean over mixed tasks (>= 1 won and >= 1 lost episode) of mean(phi | lost) - mean(phi | won), with a task-bootstrap 90% CI
    -> (ic, lo90, hi90); (0.0, 0.0, 0.0) if there is no mixed task."""
    phi = np.asarray(phi, float); by = collections.defaultdict(lambda: ([], []))
    for i, e in enumerate(eps): by[e["task"]][0 if e["won"] else 1].append(phi[i])
    diffs = np.array([np.mean(l) - np.mean(w) for w, l in by.values() if w and l], float)
    if len(diffs) == 0: return 0.0, 0.0, 0.0
    lo, hi = boot(diffs, B, seed)
    return float(diffs.mean()), lo, hi


def beta_stats(a, b, lam=0.25, kappa=0.5):
    """node with a wins / b losses: posterior Beta(1 + a, 1 + b); p = posterior mean, var = posterior variance, g = p - 1, h = p(1 - p).
    priority = g^2 / (h + lam) + kappa * sd: the XGBoost Newton gain of the node (consistent failures, small h, rank FIRST -- systematic
    errors are what a rubric can fix; |g|*h would push them down) plus an exploration bonus for few observations."""
    al, be = 1.0 + a, 1.0 + b; p = al / (al + be); var = al * be / ((al + be) ** 2 * (al + be + 1)); g, h = p - 1, p * (1 - p)
    return {"p": p, "var": var, "g": g, "h": h, "priority": g * g / (h + lam) + kappa * var ** 0.5}


def signflip(x, B=20000, seed=0):
    x = np.asarray(x, float); rng = np.random.default_rng(seed); obs = abs(x.mean())
    return float(((np.abs((rng.choice([-1, 1], (B, len(x))) * x).mean(1)) >= obs - 1e-12).mean()))


def boot(x, B=5000, seed=0):
    x = np.asarray(x, float); rng = np.random.default_rng(seed); m = x[rng.integers(0, len(x), (B, len(x)))].mean(1)
    return float(np.quantile(m, 0.05)), float(np.quantile(m, 0.95))
