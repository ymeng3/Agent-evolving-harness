"""CC-BOOST shared pieces (docs/preregs/CC_BOOST_RUBRIC_PREREG.md): landmark prefixes, detector sandbox, ridge-logistic model,
task-grouped cross-validation. A rubric dimension is an executable detector `detect(steps) -> float` over the first L cells."""
import ast, json, math, os, random, re, signal, threading
import numpy as np

L = int(os.environ.get("BOOST_L", "15"))
ALLOWED_IMPORTS = {"re", "json", "math", "random", "collections", "itertools", "string"}
FORBIDDEN = {"open", "exec", "eval", "__import__", "compile", "globals", "locals", "getattr", "setattr", "delattr", "vars", "input", "breakpoint", "exit", "quit"}
_CALL_DONE = re.compile(r"apis\.supervisor\.complete_task\s*\(")


def load_runs(paths):
    """One record per (run, task). Detectors only ever see `cells` = the first L cells with code / output tail / error flag /
    reply tail; goal-check fields (gp, gf, G, harm_fail) are dropped here so they cannot leak into a detector."""
    recs = []
    for p in paths:
        d = json.load(open(p))
        crashed = d.get("crashed") or [None] * len(d["games"])
        for t, w, tr, cr in zip(d["games"], d["won"], d["traj"], crashed):
            if cr: continue
            cells = [{"i": s["step"], "code": s.get("code") or "", "out": s.get("out") or "", "error": bool(s.get("exec_error")), "reply": s.get("resp") or ""} for s in tr]
            early_done = any(_CALL_DONE.search(c["code"]) for c in cells[:L])   # an actual call, not a docs lookup that mentions the name
            recs.append({"task": t, "seed": d["seed"], "tag": d["tag"], "y": int(bool(w)), "n_cells": len(cells), "cells": cells[:L],
                         "at_risk": len(cells) > L and not early_done})   # landmark set: still running at cell L, so length cannot leak the outcome
    return recs


def compile_detector(src):
    """Same sandbox rules as harness patches: allowed imports only, no I/O / reflection / dunder access. Must define detect(steps)."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            if any(n not in ALLOWED_IMPORTS for n in names): raise ValueError(f"import not allowed: {names}")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN: raise ValueError(f"forbidden name {node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"): raise ValueError("dunder attribute")
    if not any(isinstance(n, ast.FunctionDef) and n.name == "detect" for n in tree.body): raise ValueError("no top-level detect(steps)")
    ns = {}
    with _alarm_guard(5.0):
        try: exec(compile(src, "<detector>", "exec"), ns)
        except _Timeout: raise ValueError("module-level code timed out")
    return ns["detect"]


class _Timeout(BaseException): pass   # BaseException so a detector's own `except Exception` cannot swallow it
def _alarm(sig, frame): raise _Timeout()


class _alarm_guard:
    """repeating SIGALRM while active (main thread on POSIX only; no-op elsewhere)."""
    def __init__(self, s): self.s = s; self.on = hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread()
    def __enter__(self):
        if self.on: self.old = signal.signal(signal.SIGALRM, _alarm); signal.setitimer(signal.ITIMER_REAL, self.s, self.s)
    def __exit__(self, *a):
        if self.on: signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, self.old)
        return False


def run_detector(fn, recs, per_call_s=2.0):
    """-> (values array with nan for errors/timeouts, n_errors). Each call sees a fresh copy of the cells."""
    vals, errs = [], 0
    for r in recs:
        try:
            with _alarm_guard(per_call_s):
                v = float(fn([dict(c) for c in r["cells"]]))
            if not math.isfinite(v): raise ValueError("non-finite")
        except KeyboardInterrupt:
            raise
        except BaseException:   # includes _Timeout and SystemExit raised by a detector
            v = float("nan"); errs += 1
        vals.append(v)
    return np.array(vals, dtype=float), errs


def standardize(F_tr, F_te=None):
    """median-impute nan, z-score with train stats, clip to [-5, 5]; constant train columns become 0."""
    F_tr = np.array(F_tr, dtype=float, copy=True); F_te = None if F_te is None else np.array(F_te, dtype=float, copy=True)
    if F_tr.shape[1] == 0: return F_tr, F_te
    med = np.nanmedian(np.where(np.isnan(F_tr).all(0, keepdims=True), 0.0, F_tr), axis=0)
    for M in (F_tr, F_te):
        if M is None: continue
        bad = np.isnan(M); M[bad] = np.take(med, np.nonzero(bad)[1])
    mu, sd = F_tr.mean(0), F_tr.std(0); sd = np.where(sd < 1e-9, 1.0, sd)
    Z_tr = np.clip((F_tr - mu) / sd, -5, 5); Z_tr[:, F_tr.std(0) < 1e-9] = 0.0
    Z_te = None if F_te is None else np.clip((F_te - mu) / sd, -5, 5)
    if Z_te is not None: Z_te[:, F_tr.std(0) < 1e-9] = 0.0
    return Z_tr, Z_te


def fit_logit(Z, y, lam=1.0, iters=100):
    """ridge-logistic (intercept unpenalised) by Newton; returns [b, w_1..w_k]."""
    n, k = Z.shape; X = np.hstack([np.ones((n, 1)), Z]); w = np.zeros(k + 1)
    R = lam * np.eye(k + 1); R[0, 0] = 1e-8
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30))); W = p * (1 - p)
        step = np.linalg.solve((X * W[:, None]).T @ X + R, X.T @ (p - y) + R @ w); w -= step
        if np.abs(step).max() < 1e-9: break
    return w


def predict(w, Z): return 1 / (1 + np.exp(-np.clip(w[0] + Z @ w[1:], -30, 30)))
def logloss(y, p): p = np.clip(p, 1e-6, 1 - 1e-6); return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
def brier(y, p): return float(np.mean((p - y) ** 2))


def auc(y, s):
    """Mann-Whitney AUC with average ranks for ties; nan if one class is empty."""
    y = np.asarray(y); s = np.asarray(s, dtype=float); n1 = int(y.sum()); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return float("nan")
    order = np.argsort(s, kind="mergesort"); ranks = np.empty(len(s)); i = 0; ss = s[order]
    while i < len(s):
        j = i
        while j + 1 < len(s) and ss[j + 1] == ss[i]: j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1; i = j + 1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def group_folds(groups, k, seed):
    u = sorted(set(groups)); rng = random.Random(seed); rng.shuffle(u); f = {g: i % k for i, g in enumerate(u)}
    return np.array([f[g] for g in groups])


def cv_logloss(F, y, groups, reps=5, k=5, lam=1.0):
    """grouped (by task) repeated k-fold CV log-loss of the ridge-logistic on raw feature matrix F (n x m, m may be 0).
    -> (mean log-loss over repeats, out-of-fold p averaged over repeats)."""
    F = np.asarray(F, dtype=float).reshape(len(y), -1); lls, P = [], np.zeros(len(y))
    for rep in range(reps):
        fo = group_folds(groups, k, 1000 + rep); p = np.zeros(len(y))
        for j in range(k):
            tr, te = fo != j, fo == j
            if te.sum() == 0: continue
            Z_tr, Z_te = standardize(F[tr], F[te]); p[te] = predict(fit_logit(Z_tr, y[tr], lam), Z_te)
        lls.append(logloss(y, p)); P += p / reps
    return float(np.mean(lls)), P


def fit_eval(F_tr, y_tr, F_te, y_te, lam=1.0):
    """fit on train, score on held-out; returns metrics + weights (on standardised features)."""
    Z_tr, Z_te = standardize(F_tr, F_te); w = fit_logit(Z_tr, y_tr, lam); p = predict(w, Z_te)
    return {"logloss": logloss(y_te, p), "auc": auc(y_te, p), "brier": brier(y_te, p), "w": w.tolist()}, p


def cluster_bootstrap_diff(groups, a, b, B=2000, seed=0):
    """paired bootstrap over task clusters of mean(a - b) (per-trajectory losses); -> (diff, lo90, hi90)."""
    groups = np.asarray(groups); u = sorted(set(groups.tolist())); idx = {g: np.nonzero(groups == g)[0] for g in u}
    d = np.asarray(a) - np.asarray(b); rng = np.random.default_rng(seed); stats = []
    for _ in range(B):
        pick = rng.choice(len(u), len(u), replace=True); ii = np.concatenate([idx[u[j]] for j in pick]); stats.append(d[ii].mean())
    return float(d.mean()), float(np.quantile(stats, 0.05)), float(np.quantile(stats, 0.95))


def per_traj_logloss(y, p): p = np.clip(p, 1e-6, 1 - 1e-6); return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def window(cells, code_n=200, out_n=200):
    return "\n".join(f"[cell {c['i']}]{' (ERROR)' if c['error'] else ''} {c['code'][:code_n]}\n  -> {c['out'][:out_n]}" for c in cells)


FIXED_DETECTORS = {
    "error_rate": ("fraction of the first cells whose execution failed",
                   "def detect(steps):\n    return sum(1 for s in steps if s['error']) / max(1, len(steps))\n"),
    "error_streak": ("longest run of consecutive failed cells",
                     "def detect(steps):\n    best = cur = 0\n    for s in steps:\n        cur = cur + 1 if s['error'] else 0\n        best = max(best, cur)\n    return best\n"),
    "docs_share": ("fraction of cells that query api_docs",
                   "def detect(steps):\n    return sum(1 for s in steps if 'api_docs' in s['code']) / max(1, len(steps))\n"),
    "repeat_cell": ("largest number of times one identical cell (whitespace-normalised) is repeated",
                    "def detect(steps):\n    import collections\n    c = collections.Counter(' '.join(s['code'].split()) for s in steps)\n    return max(c.values()) if c else 0\n"),
    "apps_touched": ("number of distinct apps called (excluding api_docs and supervisor)",
                     "def detect(steps):\n    import re\n    apps = set()\n    for s in steps:\n        apps.update(re.findall(r'apis\\.([a-z_]+)\\.', s['code']))\n    return len(apps - {'api_docs', 'supervisor'})\n"),
    "empty_out": ("fraction of cells whose output is empty or None",
                  "def detect(steps):\n    return sum(1 for s in steps if s['out'].strip() in ('', 'None')) / max(1, len(steps))\n"),
}
