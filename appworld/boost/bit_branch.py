"""BIT Unit F (docs/design/BIT_IMPLEMENTATION_PLAN.md): branch-at-fire build, readout + admission, validation arm.
build   For each kept candidate (screen.json "kept" + --force-cid) re-simulate its compiled patch on the base H1 discovery logs
        (bit_rubric.simulate; crashed / replayed episodes skipped) and turn every first firing (episode, step k) into a branch state:
          note        replay codes[:k] in both arms; cand = patches_ccdiag/BRANCH_NOTE.py + BOS_HINTS {tid: note}, none = --patch none
          block_once  replay_none = codes[:k+1] (logged cell k executed); replay_cand = codes[:k] + [{"exec": print(<block note>),
                      "shown": codes[k]}] (cell k shown but blocked, exactly what the compiled patch emits online); both --patch none
        One directory <cid>_o<seed>/ per (candidate, origin seed): tasks.json, replay_none.json, replay_cand.json, [hints_cand.json],
        meta.json {tid: {eid, k, kind, note, logged_won, ...}}; plus manifest.json and jobs.txt (one qsub line per job).
        The build runs LOCALLY and emits SERVER paths: every path in jobs.txt is <--server-out>/<dir>/..., where --server-out defaults to
        <--server-root>/<--out relative to appworld/> (or <--server-root>/bit/<R>/branch if --out lies outside appworld/). Sync the --out
        directory to that server location before queueing jobs.txt (jobs run in $CC_REPO/appworld, see tools/queue/qrunner.sh).
readout Per state d = mean over reps of cand won - mean of none won (and d_G on G); states of a task averaged; a-bar, task-bootstrap 90% CI,
        sign-flip p, Holm across the K candidates read out; split by logged won/lost; manipulation check; tau = s * a-bar (s from
        screen.json, else the build's simulated fire rate). Admission: boot90_lo > 0 and mean > 0 and n_tasks >= 3 -> admitted.json.
valarm  Compile the admitted specs (descending a-bar) into appworld/patches_ccbit/<R>_ADMITTED.py; print the val qsub lines and the
        multi_metric_readout command.
usage: python boost/bit_branch.py build --screen bit/R1/screen.json --cands bit/R1/cands_P1.jsonl --runs A.json,B.json --instr instr.json
                                        --out bit/R1/branch --round R1 --env-file base_env.txt [--force-cid D10_ref --refs boost/bit_refs/D10_ref.json]
       python boost/bit_branch.py readout --build bit/R1/branch --results results --screen bit/R1/screen.json [--alpha 0.10]
       python boost/bit_branch.py valarm --admitted bit/R1/branch/admitted.json --round R1 --env-file base_env.txt
                                         --base-val results/CC_H1_F0_val_seed1.json,results/CC_H1_F0_val_seed2.json
Gaia2 (GAIA2_ADAPTER_PLAN U6): build / valarm --harness-cmd "env -u PYTHONPATH /root/autodl-tmp/cc/are-env/bin/python ../gaia2/bos_gaia2.py"
(jobs still run with cwd appworld/; never put cd in it); readout --results ../gaia2/results; valarm --results ../gaia2/results."""
import argparse, collections, json, os, posixpath, re, shlex, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); AW = os.path.dirname(HERE)
if HERE not in sys.path: sys.path.insert(0, HERE)
from bit_common import boot, load_episodes, signflip   # noqa: E402

SERVER_ROOT = "/root/autodl-tmp/cc/Agent-evolving-harness/appworld"
BLOCK_PREFIX = "[harness note] Your cell was NOT executed. "   # = bit_rubric._BLOCK_T
NOTE_PATCH = "patches_ccdiag/BRANCH_NOTE.py"
OWN_ENV = ("BOS_TASKS", "BOS_REPLAY", "BOS_HINTS")   # set per job; dropped from the base env line
HARNESS_CMD = "python bos_appworld_v3.py"   # --harness-cmd default; shlex-split into the job line before "eval ..."
GAIA2_CMD = "env -u PYTHONPATH /root/autodl-tmp/cc/are-env/bin/python ../gaia2/bos_gaia2.py"


# ---------------------------------------------------------------- shared
def read_env(path):
    """the base job's env assignments. The file may hold just 'K=V K=V ...' or a whole job line (qsub.sh TAG K=V ... python ...):
    only the K=V tokens before the command are kept, minus BOS_TASKS / BOS_REPLAY / BOS_HINTS."""
    toks = shlex.split(" ".join(l for l in open(path, encoding="utf-8").read().splitlines() if not l.lstrip().startswith("#")))
    env, started = [], False
    for t in toks:
        if "=" in t and t.split("=", 1)[0].isidentifier():
            started = True
            if t.split("=", 1)[0] not in OWN_ENV: env.append(t)
        elif started: break   # first non-assignment after the assignments = the command
    return env


def load_screen(path):
    s = json.load(open(path, encoding="utf-8")); cands = s.get("candidates") or []
    return s, {c.get("cid"): c for c in cands if c.get("cid") is not None}


def harness_cmd(a):
    """--harness-cmd as job-line tokens (re-quoted, so a token with spaces survives the qsub line)."""
    toks = shlex.split(a.harness_cmd)
    if not toks or "cd" in toks: sys.exit(f"--harness-cmd must be the harness command run from appworld/ (no cd): {a.harness_cmd!r}")
    return [shlex.quote(t) for t in toks]


def holm(ps):
    """Holm step-down adjusted p-values (same order as ps)."""
    ps = np.asarray(ps, float); o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (m - r) * ps[i])); adj[i] = run
    return adj.tolist()


# ---------------------------------------------------------------- build
def resolve_specs(cids, screen_c, cands_paths, refs_paths):
    """cid -> (spec, is_ref). Lookup order: screen.json candidate "spec" (bit_screen does not store it), --cands JSONL line,
    --refs file (by file stem, spec name, ref_<name> or cid)."""
    jl = {}
    for p in [x for x in (cands_paths or "").split(",") if x]:
        for line in open(p, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if r.get("cid") and r.get("spec"): jl[r["cid"]] = r
    refs = {}
    for p in [x for x in (refs_paths or "").split(",") if x]:
        sp = json.load(open(p, encoding="utf-8")); sp = sp.get("spec", sp)
        for key in (os.path.splitext(os.path.basename(p))[0], sp.get("name"), "ref_" + str(sp.get("name")), sp.get("cid")):   # ref_<name> = bit_screen's ref cid
            if key: refs[key] = sp
    out = {}
    for cid in cids:
        c = screen_c.get(cid) or {}
        if c.get("spec"): out[cid] = (c["spec"], bool(c.get("ref") or c["spec"].get("ref")))
        elif cid in jl: out[cid] = (jl[cid]["spec"], False)
        elif cid in refs: out[cid] = (refs[cid], True)
        else: print(f"  ! {cid}: no spec found in screen.json / --cands / --refs; skipped")
    return out


def server_out_dir(a):
    if a.server_out: return a.server_out.rstrip("/")
    rel = os.path.relpath(os.path.abspath(a.out), AW)
    if rel.startswith(".."):
        d = posixpath.join(a.server_root, "bit", a.round, "branch")
        print(f"  ! --out is outside appworld/; server paths default to {d} (sync --out there or pass --server-out)")
        return d
    return posixpath.join(a.server_root, rel.replace(os.sep, "/"))


def build(a):
    import bit_rubric as BR
    screen, screen_c = load_screen(a.screen)
    kept = list(screen.get("kept") or []) + [c for f in a.force_cid for c in f.split(",") if c]
    kept = list(dict.fromkeys(kept))
    if not kept: sys.exit("nothing to build: screen.json kept list is empty and no --force-cid")
    eps_all = load_episodes(a.runs, a.instr)
    bad = sorted({e["tag"] + f"_s{e['seed']}" for e in eps_all if not e["harness_h1"]})
    if bad: sys.exit(f"base logs must be harness_h1 (exact replay without evaluate): {bad}")
    eps = [e for e in eps_all if not e["crashed"] and not e["has_replay"]]
    print(f"base: {len(eps_all)} episodes, {len(eps)} usable (not crashed, no replayed steps), {sum(e['won'] for e in eps)} won")
    max_steps = max(json.load(open(p, encoding="utf-8")).get("max_steps", 30) for p in a.runs.split(",") if p)
    specs = resolve_specs(kept, screen_c, a.cands, a.refs)
    # boosting round >= 2: the base harness already contains admitted trees (h_r = h_0 + k_1 + ...). Both arms must run with them:
    # none arm / block cand arm -> --patch <round>_BASE.py; note cand arm -> base trees + the candidate compiled together (its detector
    # fires at the first live step after the replayed prefix, as in the simulation).
    base_specs = [json.load(open(x, encoding="utf-8")) for x in a.base_specs.split(",") if x]
    base_patch = None; pdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "patches_ccbit")
    if base_specs:
        os.makedirs(pdir, exist_ok=True); base_patch = f"patches_ccbit/{a.round}_BASE.py"
        open(os.path.join(pdir, f"{a.round}_BASE.py"), "w", encoding="utf-8").write(BR.compile_patch(base_specs, max_steps))
        print(f"base trees: {[b.get('name') for b in base_specs]} -> {base_patch}")
    env = read_env(a.env_file); srv = server_out_dir(a)
    qsub = a.qsub or ("bash " + posixpath.join(posixpath.dirname(a.server_root.rstrip("/")), "tools", "queue", "qsub.sh"))
    os.makedirs(a.out, exist_ok=True); byeid = {e["eid"]: e for e in eps}
    manifest = {"round": a.round, "runs": a.runs, "server_out": srv, "env": env, "reps": a.reps, "max_steps": max_steps,
                "screen": a.screen, "cands": [], "jobs": []}
    jobs = []
    for cidx, cid in enumerate(kept):
        if cid not in specs: continue
        spec, is_ref = specs[cid]; kind = spec["kind"]; ctag = f"c{cidx:02d}"
        try: res = BR.simulate(BR.compile_patch([spec], max_steps), eps, stop_at_first=True, timeout_s=a.timeout)
        except (ValueError, BR.SimulationError) as e: print(f"  ! {cid}: invalid ({str(e)[:200]}); skipped"); continue
        fired = [(eid, r["fires"][0]) for eid, r in res.items() if r["fires"]]
        states = {}   # (seed, tid) -> state; first firing per (tid, origin seed)
        for eid, f in sorted(fired, key=lambda x: (byeid[x[0]]["seed"], x[0])):
            e = byeid[eid]; key = (e["seed"], e["task"])
            if key in states: continue
            i = next((j for j, s in enumerate(e["steps"]) if s["k"] == f["k"]), None)
            if i is None: print(f"  ! {cid} {eid}: fire step {f['k']} not in the log; skipped"); continue
            codes = [s["code"] or "" for s in e["steps"]]; note = (f.get("note") or spec["note"]).strip()
            if kind == "block_once":
                rn = codes[:i + 1]; rc = codes[:i] + [{"exec": "print(" + repr(BLOCK_PREFIX + note) + ")", "shown": codes[i]}]
            else: rn = rc = codes[:i]
            states[key] = {"eid": eid, "k": f["k"], "kind": kind, "note": note, "logged_won": e["won"], "logged_G": e["G"],
                           "n_steps": len(e["steps"]), "no_exec_in_prefix": sum(1 for s in e["steps"][:i] if s["no_exec"]),
                           "_rn": rn, "_rc": rc}
        n_all = len(states)
        if n_all > a.max_states:   # deterministic subsample, spread over seeds and tasks
            keys = sorted(states); rng = np.random.default_rng(0); keep = {keys[j] for j in rng.permutation(len(keys))[:a.max_states]}
            states = {k: v for k, v in states.items() if k in keep}
        s_sim = len(fired) / max(len(eps), 1)
        crec = {"cid": cid, "cidx": ctag, "name": spec.get("name"), "kind": kind, "ref": is_ref, "spec": spec, "s_sim": s_sim,
                "n_fired_eps": len(fired), "n_fired_lost": sum(1 for eid, _ in fired if not byeid[eid]["won"]),
                "n_states_all": n_all, "n_states": len(states), "dirs": []}
        for seed in sorted({k[0] for k in states}):
            m = {t: v for (s, t), v in states.items() if s == seed}; name = re.sub(r"[^A-Za-z0-9_.-]", "_", cid) + f"_o{seed}"; dd = os.path.join(a.out, name)
            os.makedirs(dd, exist_ok=True); sd = posixpath.join(srv, name)
            json.dump(sorted(m), open(os.path.join(dd, "tasks.json"), "w"))
            json.dump({t: v["_rn"] for t, v in m.items()}, open(os.path.join(dd, "replay_none.json"), "w"))
            json.dump({t: v["_rc"] for t, v in m.items()}, open(os.path.join(dd, "replay_cand.json"), "w"))
            if kind == "note": json.dump({t: v["note"] for t, v in m.items()}, open(os.path.join(dd, "hints_cand.json"), "w"), indent=1)
            json.dump({t: {k: x for k, x in v.items() if not k.startswith("_")} for t, v in m.items()},
                      open(os.path.join(dd, "meta.json"), "w"), indent=1)
            crec["dirs"].append({"dir": name, "seed": seed, "n": len(m), "logged_lost": sum(1 for v in m.values() if not v["logged_won"])})
            for arm in ("none", "cand"):
                for rep in range(a.reps):
                    tag = f"CC_BIT_{a.round}_{ctag}_{arm}_o{seed}_r{rep}"
                    ev = [f"BOS_TASKS={sd}/tasks.json", f"BOS_REPLAY={sd}/replay_{arm}.json"]
                    patch = base_patch or "none"
                    if arm == "cand" and kind == "note":
                        if base_patch:
                            patch = f"patches_ccbit/{a.round}_{ctag}_CAND.py"
                            open(os.path.join(pdir, f"{a.round}_{ctag}_CAND.py"), "w", encoding="utf-8").write(BR.compile_patch(base_specs + [spec], max_steps))
                        else: ev.append(f"BOS_HINTS={sd}/hints_cand.json"); patch = NOTE_PATCH
                    jobs.append(" ".join([qsub, tag] + env + ev + harness_cmd(a) + ["eval", "--patch", patch,
                                                                    "--seed", str(seed), "--tag", tag, "--workers", str(a.workers)]))
                    manifest["jobs"].append({"tag": tag, "cid": cid, "cidx": ctag, "arm": arm, "seed": seed, "rep": rep, "dir": name})
        manifest["cands"].append(crec)
        print(f"{ctag} {cid:28s} {kind:10s} fired {len(fired)} eps ({crec['n_fired_lost']} lost) -> {len(states)} states "
              f"{[(d['seed'], d['n']) for d in crec['dirs']]}{' (capped from %d)' % n_all if n_all > len(states) else ''}")
    json.dump(manifest, open(os.path.join(a.out, "manifest.json"), "w"), indent=1)
    open(os.path.join(a.out, "jobs.txt"), "w", newline="\n").write("".join(j + "\n" for j in jobs))
    print(f"{len(jobs)} jobs -> {os.path.join(a.out, 'jobs.txt')} (server paths under {srv})")


def post_p_pos(rows, B=20000, seed=0):
    """A25: P(mean over states of (p_cand - p_none) > 0) with independent Beta(1+wins, 1+losses) posteriors per arm and state."""
    if not rows: return None
    rng = np.random.default_rng(seed)
    pc = np.stack([rng.beta(1 + r["cw"], 1 + r["cn"] - r["cw"], B) for r in rows]); pn = np.stack([rng.beta(1 + r["nw"], 1 + r["nn"] - r["nw"], B) for r in rows])
    return float(((pc - pn).mean(0) > 0).mean())


# ---------------------------------------------------------------- readout
def load_result(path):
    """-> {tid: (won, G, traj)} for non-crashed tasks, or None if the file does not exist yet."""
    if not os.path.exists(path): return None
    d = json.load(open(path, encoding="utf-8")); n = len(d["games"])
    out = {}
    for t, w, g, cr, tr in zip(d["games"], d["won"], d.get("G") or [None] * n, d.get("crashed") or [None] * n, d.get("traj") or [None] * n):
        if not cr: out[t] = (float(w), float(g) if g is not None else float(w), tr or [])
    return out


def manipulated(kind, k, tr):
    """was the intervention visible in this cand-arm continuation? note: the first live step's prompt changed (pc); block_once: the
    last replayed cell was the blocked one (shown != exec) and printed the harness note. None if the trajectory is not logged."""
    if not tr: return None
    if kind == "block_once":
        s = tr[k] if len(tr) > k else None
        return bool(s and s.get("replayed") and "shown" in s and BLOCK_PREFIX.strip() in (s.get("out") or ""))
    s = tr[k] if len(tr) > k else None
    return bool(s and not s.get("replayed") and s.get("pc"))


def stats(x):
    x = np.asarray(x, float)
    if len(x) == 0: return {"n": 0, "mean": None, "lo90": None, "hi90": None, "p": None}
    lo, hi = boot(x) if len(x) > 1 else (float(x[0]), float(x[0]))
    return {"n": int(len(x)), "mean": float(x.mean()), "lo90": lo, "hi90": hi, "p": signflip(x)}


def readout(a):
    man = json.load(open(os.path.join(a.build, "manifest.json"), encoding="utf-8"))
    screen_c = load_screen(a.screen)[1] if a.screen else {}
    res = []
    for c in man["cands"]:
        cid = c["cid"]; rows = []; missing = 0; manip = []
        for dd in c["dirs"]:
            meta = json.load(open(os.path.join(a.build, dd["dir"], "meta.json"), encoding="utf-8"))
            arm = {"none": [], "cand": []}
            for j in man["jobs"]:
                if j["cid"] == cid and j["dir"] == dd["dir"]:
                    r = load_result(os.path.join(a.results, f"{j['tag']}_seed{j['seed']}.json"))
                    if r is not None: arm[j["arm"]].append(r)
            for t, m in meta.items():
                cw = [r[t] for r in arm["cand"] if t in r]; nw = [r[t] for r in arm["none"] if t in r]
                if not cw or not nw: missing += 1; continue
                rows.append({"task": t, "seed": dd["seed"], "logged_won": m["logged_won"],
                             "cw": int(sum(x[0] for x in cw)), "cn": len(cw), "nw": int(sum(x[0] for x in nw)), "nn": len(nw),
                             "d": np.mean([x[0] for x in cw]) - np.mean([x[0] for x in nw]),
                             "dG": np.mean([x[1] for x in cw]) - np.mean([x[1] for x in nw]),
                             "cand": np.mean([x[0] for x in cw]), "none": np.mean([x[0] for x in nw])})
                manip += [v for v in (manipulated(m["kind"], m["k"], x[2]) for x in cw) if v is not None]

        def task_mean(sel, key):
            by = collections.defaultdict(list)
            for r in rows:
                if sel(r): by[r["task"]].append(r[key])
            return [float(np.mean(v)) for _, v in sorted(by.items())]
        st = stats(task_mean(lambda r: True, "d")); sg = stats(task_mean(lambda r: True, "dG"))
        sc = screen_c.get(cid) or {}; s = sc.get("s", c.get("s_sim")); s_src = "screen" if "s" in sc else "build_sim"
        res.append({"cid": cid, "cidx": c["cidx"], "name": c["name"], "kind": c["kind"], "ref": c["ref"], "n_states": len(rows),
                    "n_missing": missing, "n_tasks": st["n"], "a_bar": st["mean"], "lo90": st["lo90"], "hi90": st["hi90"], "p": st["p"],
                    "G": sg, "won_split": stats(task_mean(lambda r: r["logged_won"], "d")),
                    "lost_split": stats(task_mean(lambda r: not r["logged_won"], "d")),
                    "win_cand": float(np.mean([r["cand"] for r in rows])) if rows else None,
                    "win_none": float(np.mean([r["none"] for r in rows])) if rows else None,
                    "manip": (float(np.mean(manip)) if manip else None), "s": s, "s_src": s_src,
                    "tau": (s * st["mean"] if s is not None and st["mean"] is not None else None), "spec": c["spec"],
                    "p_pos": post_p_pos(rows), "memo_flag": bool(sc.get("memo_flag"))})
    have = [r for r in res if r["p"] is not None]
    for r, h in zip(have, holm([r["p"] for r in have]) if have else []): r["p_holm"] = h
    f = lambda v, fmt="+.3f": "   -  " if v is None else format(v, fmt)
    print(f"{'cidx':4s} {'cid':26s} {'kind':10s} st/miss tasks  a_bar  [90% CI]          p   holm | dG     | lost-split won-split | manip   tau  adm")
    for r in res:
        if a.rule == "posterior":   # prereg A25 (rounds >= R1)
            r["admitted"] = bool(r["p_pos"] is not None and r["p_pos"] >= 0.90 and (r["a_bar"] or 0) > 0 and r["n_states"] >= 4 and not r["memo_flag"])
        else:                       # prereg A23 (R0)
            r["admitted"] = bool(r["lo90"] is not None and r["lo90"] > 0 and r["a_bar"] > 0 and r["n_tasks"] >= 3)
        print(f"{r['cidx']:4s} {r['cid'][:26]:26s} {r['kind']:10s} {r['n_states']:3d}/{r['n_missing']:<3d} {r['n_tasks']:4d} {f(r['a_bar'])} "
              f"[{f(r['lo90'])},{f(r['hi90'])}] {f(r['p'], '.3f')} {f(r.get('p_holm'), '.3f')} | {f(r['G']['mean'])} | "
              f"{f(r['lost_split']['mean'])}(n={r['lost_split']['n']}) {f(r['won_split']['mean'])}(n={r['won_split']['n']}) | "
              f"{f(r['manip'], '.2f')} {f(r['tau'])} {'YES' if r['admitted'] else 'no'}{' (ref)' if r['ref'] else ''}  P(a>0)={f(r['p_pos'], '.2f')}{' MEMO' if r['memo_flag'] else ''}")
    adm = sorted([r for r in res if r["admitted"] and (a.admit_refs or not r["ref"])], key=lambda r: -r["a_bar"])
    out = a.out or os.path.join(a.build, "admitted.json")
    json.dump({"params": {"build": a.build, "results": a.results, "screen": a.screen, "alpha": a.alpha, "round": man["round"],
                          "rule": ("P(a>0) >= 0.90 (state-level Beta posteriors) and mean > 0 and n_states >= 4 and no memo flag" if a.rule == "posterior"
                                   else "boot90_lo > 0 and mean > 0 and n_tasks >= 3"), "admit_refs": a.admit_refs},
               "results": [{k: v for k, v in r.items() if k != "spec"} for r in res],
               "admitted": [{"cid": r["cid"], "a_bar": r["a_bar"], "lo90": r["lo90"], "tau": r["tau"], "p_holm": r.get("p_holm"),
                             "spec": r["spec"]} for r in adm]}, open(out, "w"), indent=1)
    print(f"Holm at alpha={a.alpha}: {[r['cid'] for r in have if r['p_holm'] <= a.alpha]} | admitted {[r['cid'] for r in adm]} -> {out}")


# ---------------------------------------------------------------- valarm
def valarm(a):
    import bit_rubric as BR
    d = json.load(open(a.admitted, encoding="utf-8")); adm = sorted(d["admitted"], key=lambda r: -(r["a_bar"] or 0))
    if not adm: sys.exit("no admitted specs: nothing to validate")
    base_specs = [json.load(open(x, encoding="utf-8")) for x in a.base_specs.split(",") if x]   # trees already in the base (round >= 2) first
    src = BR.compile_patch(base_specs + [r["spec"] for r in adm], a.max_steps)
    rel = f"patches_ccbit/{a.round}_ADMITTED.py"; path = os.path.join(AW, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "w", encoding="utf-8", newline="\n").write(src)
    print(f"# compiled {len(adm)} spec(s) {[r['cid'] for r in adm]} -> {path} (sync to the server before queueing)")
    env = read_env(a.env_file) + [f"BOS_TASKS={a.val_tasks}"]
    qsub = a.qsub or ("bash " + posixpath.join(posixpath.dirname(a.server_root.rstrip("/")), "tools", "queue", "qsub.sh"))
    tag = f"CC_BIT_{a.round}_ADM_val"; seeds = [int(s) for s in a.seeds.split(",")]
    for s in seeds:
        print(" ".join([qsub, tag] + env + harness_cmd(a) + ["eval", "--patch", rel, "--seed", str(s), "--tag", tag,
                                            "--workers", str(a.workers)]))
    arm = ",".join(posixpath.join(a.results, f"{tag}_seed{s}.json") for s in seeds)
    print(f"# after both finish (in appworld/):\npython boost/multi_metric_readout.py --base {a.base_name}={a.base_val} --arm {a.round}_ADM={arm}")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--screen", required=True); b.add_argument("--cands", default="")
    b.add_argument("--refs", default=""); b.add_argument("--runs", required=True); b.add_argument("--instr", required=True)
    b.add_argument("--out", required=True); b.add_argument("--round", required=True); b.add_argument("--reps", type=int, default=1)
    b.add_argument("--max-states", type=int, default=40); b.add_argument("--env-file", required=True)
    b.add_argument("--force-cid", action="append", default=[]); b.add_argument("--server-root", default=SERVER_ROOT)
    b.add_argument("--server-out", default=""); b.add_argument("--qsub", default=""); b.add_argument("--workers", type=int, default=8)
    b.add_argument("--timeout", type=float, default=300)
    b.add_argument("--base-specs", default="", help="comma list of spec JSONs of trees already in the base harness (boosting round >= 2)")
    b.add_argument("--harness-cmd", default=HARNESS_CMD, help=f"harness command of the job lines (Gaia2: {GAIA2_CMD!r})")
    r = sub.add_parser("readout"); r.add_argument("--build", required=True); r.add_argument("--results", default="results")
    r.add_argument("--screen", default=""); r.add_argument("--alpha", type=float, default=0.10); r.add_argument("--out", default="")
    r.add_argument("--admit-refs", action="store_true", help="let reference specs (positive controls) into admitted.json")
    r.add_argument("--rule", choices=["bootstrap", "posterior"], default="bootstrap", help="A23 bootstrap rule (R0) or A25 posterior rule (>= R1)")
    v = sub.add_parser("valarm"); v.add_argument("--admitted", required=True); v.add_argument("--round", required=True)
    v.add_argument("--env-file", required=True); v.add_argument("--val-tasks", default="tasks_challenge_val50.json")
    v.add_argument("--seeds", default="1,2"); v.add_argument("--base-val", default="results/CC_H1_F0_val_seed1.json,results/CC_H1_F0_val_seed2.json")
    v.add_argument("--base-name", default="BASE"); v.add_argument("--max-steps", type=int, default=30)
    v.add_argument("--server-root", default=SERVER_ROOT); v.add_argument("--qsub", default=""); v.add_argument("--workers", type=int, default=8)
    v.add_argument("--base-specs", default="", help="comma list of spec JSONs of trees already in the base harness (compiled first)")
    v.add_argument("--harness-cmd", default=HARNESS_CMD, help=f"harness command of the job lines (Gaia2: {GAIA2_CMD!r})")
    v.add_argument("--results", default="results", help="results dir of the val runs, relative to appworld/ (Gaia2: ../gaia2/results)")
    a = ap.parse_args()
    {"build": build, "readout": readout, "valarm": valarm}[a.cmd](a)


if __name__ == "__main__":
    main()
