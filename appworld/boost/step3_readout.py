"""Read-outs fixed in prereg A7 / A8. Arms are lists of result files on the SAME task set (one file per seed).
usage: python boost/step3_readout.py --arm F0=a_s1.json,a_s2.json --arm RUBRIC=b_s1.json,b_s2.json [--arm ...] --base F0
Prints per-arm success / completion / docs share / cells used, then every arm minus the base (and pairwise), using the per-task mean
over seeds as the unit: mean difference, two-sided sign-flip p, 90% task-bootstrap CI."""
import argparse, json, re
import numpy as np


def load(paths):
    runs = [json.load(open(p, encoding="utf-8")) for p in paths]; tasks = runs[0]["games"]
    for r in runs: assert sorted(r["games"]) == sorted(tasks), "different task sets"
    won = {t: np.mean([dict(zip(r["games"], r["won"]))[t] for r in runs]) for t in tasks}
    steps = [s for r in runs for tr in r["traj"] for s in tr]
    done = np.mean([any(re.search(r"apis\.supervisor\.complete_task\s*\(", s.get("code") or "") for s in tr) for r in runs for tr in r["traj"]])
    m = {"n_runs": len(runs), "success": np.mean([np.mean(r["won"]) for r in runs]), "completed": done,
         "docs_share": np.mean(["api_docs" in (s.get("code") or "") for s in steps]), "cells": np.mean([len(tr) for r in runs for tr in r["traj"]]),
         "prompt_changed": np.mean([s.get("pc", 0) for s in steps]), "free_retries": sum(s.get("free_retries", 0) for s in steps),
         "no_exec": sum(s.get("no_exec", 0) for s in steps), "default_code": sum(s.get("default_code", 0) for s in steps),
         "crashed": sum(1 for r in runs for c in (r.get("crashed") or []) if c)}
    return won, m


def signflip(d, B=20000, seed=0):
    d = np.asarray(d, float); rng = np.random.default_rng(seed); sims = (rng.choice([-1, 1], (B, len(d))) * d).mean(1)
    return float((np.abs(sims) >= abs(d.mean()) - 1e-12).mean())


def boot(d, B=5000, seed=0):
    d = np.asarray(d, float); rng = np.random.default_rng(seed); st = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(B)]
    return float(np.quantile(st, 0.05)), float(np.quantile(st, 0.95))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", action="append", required=True); ap.add_argument("--base", required=True); a = ap.parse_args()
    arms = {}
    for spec in a.arm:
        name, paths = spec.split("=", 1); arms[name] = load(paths.split(","))
    print(f"{'arm':10s} runs success completed docs_share cells prompt_changed free_retries no_exec default_code crashed")
    for n, (_, m) in arms.items():
        print(f"{n:10s} {m['n_runs']:4d} {m['success']:7.3f} {m['completed']:9.3f} {m['docs_share']:10.3f} {m['cells']:5.1f} {m['prompt_changed']:14.3f} {m['free_retries']:12d} {m['no_exec']:7d} {m['default_code']:12d} {m['crashed']:7d}")
    names = list(arms); tasks = sorted(arms[a.base][0])
    pairs = [(n, a.base) for n in names if n != a.base] + [(x, y) for i, x in enumerate(names) for y in names[i + 1:] if a.base not in (x, y)]
    for x, y in pairs:
        d = np.array([arms[x][0][t] - arms[y][0][t] for t in tasks]); lo, hi = boot(d)
        print(f"{x} - {y}: {d.mean():+.3f} success (per-task mean over seeds), 90% CI [{lo:+.3f}, {hi:+.3f}], sign-flip p = {signflip(d):.3f}, tasks better/worse {int((d > 0).sum())}/{int((d < 0).sum())}")
