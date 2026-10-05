"""Oracle replay for the Gaia2 harness (GAIA2_ADAPTER_PLAN U7): BOS_REPLAY items built from each scenario's oracle run, so that
`bos_gaia2.py eval --replay-only` with the real (cached) judge checks env + harness + judge plumbing end to end.

Items come from scenario.oracle_run_event_log (the AGENT events ARE's oracle run executed, in time / log order, with their turn from
scenario.event_id_to_turn_idx). Oracle events of one (turn, oracle time) form one cell of App__fn(**args) calls named by AGENT-facing
tool names (App.name__fn). {{event_id[.key]}} placeholders are resolved: a reference to an earlier oracle event becomes the variable its
call was assigned to (r_<k>[...]); a reference to an ENV/USER event becomes the literal return value of that event in this run.
Timing: the oracle's time offset from its turn base (turn 0: scenario start; turn t: the oracle's send_message_to_user that ended turn
t-1) is reproduced from the replay's own turn base; SystemApp__wait_for_notification(timeout=...) cells are inserted where the target is
more than one generation step ahead (a wait ends early at the next notification, so several wait cells may be needed; at most one wait per
cell, since a notification still queued in the same cell would end a second wait at once).
The items are built by driving a G2Env in-process with exactly the harness cell sequence (advance gen -> exec -> tick -> idle if a turn
ended and turns remain -> pull; stub judge for the turn conditions), so waits are exact; the eval run then replays them unchanged.

usage (server, are-env python, PYTHONHASHSEED=0 is set by re-exec):
  python gaia2/g2_oracle_replay.py pick --per execution=20,search=20,adaptability=4,time=4 [--split gaia2/data/tasks_disc.json] --out T.json
  python gaia2/g2_oracle_replay.py build --tasks T.json --out R.json [--seed 1] [--workers 8] [--perturb none|space|suffix]
  BOS_TASKS=T.json BOS_REPLAY=R.json G2_STEPS=150 python gaia2/bos_gaia2.py eval --replay-only --patch none --seed 1 --tag CC_G2_oracle --workers 8
  python gaia2/g2_oracle_replay.py report --result gaia2/results/CC_G2_oracle_seed1.json --build R.json"""
import argparse, ast, json, math, os, re, subprocess, sys, time
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)

PH_RE = re.compile(r"^\{\{(.*?)\}\}$")
SMTU = "AgentUserInterface__send_message_to_user"
MAX_WAIT_CELLS = 12   # per group
PERTURB_ARGS = ("content",)   # --perturb: free-text args the soft (LLM) checkers read
PERTURB_SUFFIX = " Let me know if you need anything else."


def perturb_text(v, mode):
    """space: double the first inner space (invisible to a reader, but normalize_arg keeps whitespace, so the equality short-cut
    fails and the LLM checkers judge oracle-equivalent text; one-word values stay exact); suffix: append PERTURB_SUFFIX (a real edit:
    style / sanity checkers may reject it, e.g. after a signature or when the task asks for the bare answer)."""
    if mode == "space": return v.replace(" ", "  ", 1) if " " in v.strip() else v
    if mode == "suffix": return v.rstrip() + PERTURB_SUFFIX
    return v


def _literal(v):
    """repr(v) if it round-trips through ast.literal_eval, else None."""
    try:
        s = repr(v)
        return s if ast.literal_eval(s) == v else None
    except Exception:
        return None


def oracle_groups(env):
    """-> (groups, base_o, info). groups: [{"turn", "t", "events": [(event_id, tool, raw_args, resolved_args)]}] in replay order;
    base_o[t] = oracle turn-base time."""
    from are.simulation.types import EventType
    import g2_env as E
    sc = env.scenario; e2t = sc.event_id_to_turn_idx or {}
    log = list(sc.oracle_run_event_log or [])
    ag = [(i, e) for i, e in enumerate(log) if e.event_type == EventType.AGENT and getattr(e, "action", None) is not None and hasattr(e.action, "app")]
    rows, turn, n_missing = [], 0, 0
    for i, e in sorted(ag, key=lambda x: (x[1].event_time, x[0])):
        t = e2t.get(e.event_id)
        if t is None: t = turn; n_missing += 1
        tool = E._public_tool_name(e)
        raw = {k: v for k, v in (e.action.args or {}).items() if k != "self"}
        res = {k: v for k, v in (e.action.resolved_args or e.action.args or {}).items() if k != "self"}
        rows.append((t, e.event_time, i, e.event_id, tool, raw, res))
        if tool == SMTU: turn = t + 1
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    base_o = {0: env.start_time}
    for t, et, _, _, tool, _, _ in rows:
        if tool == SMTU: base_o.setdefault(t + 1, et)
    groups = []
    for t, et, _, eid, tool, raw, res in rows:
        if groups and groups[-1]["turn"] == t and abs(groups[-1]["t"] - et) < 1e-6: groups[-1]["events"].append((eid, tool, raw, res))
        else: groups.append({"turn": t, "t": et, "events": [(eid, tool, raw, res)]})
    return groups, base_o, {"n_oracle_agent_events": len(rows), "n_turn_missing": n_missing}


def group_code(g, var_of, referenced, env_return, perturb="none"):
    """App__fn(**args) lines for one group. -> (code, problems). perturb (perturb_text mode) edits free-text args so that the judge's
    equality short-cut fails and its LLM soft checkers are exercised (an exact oracle copy never reaches the LLM)."""
    lines, probs = [], []
    for eid, tool, raw, res in g["events"]:
        parts = []
        for k, v in raw.items():
            m = PH_RE.match(v.strip()) if isinstance(v, str) else None
            if m:
                ref, *path = m.group(1).split(".")
                if ref in var_of: expr = var_of[ref] + "".join(f"[{p!r}]" for p in path)
                else:
                    ok, val = env_return(ref, path)
                    expr = _literal(val) if ok else None
                    if expr is None: probs.append(f"unresolved placeholder {v} ({tool}.{k})"); expr = _literal(res.get(k))
                    if expr is None: expr = "None"
            else:
                if perturb != "none" and k in PERTURB_ARGS and isinstance(v, str) and v.strip(): v = perturb_text(v, perturb)
                expr = _literal(v)
                if expr is None: probs.append(f"non-literal arg {tool}.{k}={str(v)[:60]}"); expr = repr(str(v))
            parts.append(f"{k}={expr}")
        call = f"{tool}({', '.join(parts)})"
        if eid in referenced:
            var_of[eid] = f"r_{len(var_of)}"; call = f"{var_of[eid]} = {call}"
        lines.append(call)
    return "\n".join(lines), probs


def build_one(tid, seed=1, gen_seconds=1.0, cell_timeout=30.0, perturb="none"):
    """Drive a G2Env (stub judge) through the oracle cells exactly as bos_gaia2.play's run_cell would; -> (items, report)."""
    import g2_env as E
    from g2_exec import CodeExecutor
    t0 = time.time()
    E.install_determinism(); E.begin_episode(tid, seed)
    config, sj = E.load_scenario_json(tid)
    env = E.G2Env(sj, E.StubJudgeEngine(), gen_seconds=gen_seconds, tid=tid, seed=seed, config=config)
    groups, base_o, info = oracle_groups(env)
    referenced = set()
    for g in groups:
        for _, _, raw, _ in g["events"]:
            for v in raw.values():
                m = PH_RE.match(v.strip()) if isinstance(v, str) else None
                if m: referenced.add(m.group(1).split(".")[0])
    tools = env.tools(); ex = CodeExecutor(tools, cell_timeout_s=cell_timeout)
    env.pull_messages()   # = play(): the initial pull (task message) before step 0
    items, cells, var_of, base_r, probs = [], [], {}, {0: env.start_time}, []

    def run_cell(code):   # = bos_gaia2.play.run_cell
        n0 = env.turns_done(); env.advance(gen_seconds); t_exec = env.now(); out, inf = ex.run(code); env.tick(); n1 = env.turns_done()
        if n1 > n0 and n1 < env.nb_turns: env.idle_until_message(max(0.0, env.start_time + env.duration - env.now()))
        env.pull_messages(); items.append(code)
        cells.append({"t_exec": round(t_exec - env.start_time, 3), "err": out.startswith("Execution failed"), "out": out[:160]})
        return out, t_exec

    def ended():
        return env.turns_done() >= env.nb_turns or env.stopped() or env.time_up()

    def env_return(ref, path):
        for e in env.env.event_log.list_view():
            if e.event_id == ref:
                v = getattr(e.metadata, "return_value", None)
                for p in path:
                    if isinstance(v, dict) and p in v: v = v[p]
                    else: return False, None
                return True, v
        return False, None

    drift, n_wait, status = [], 0, "ok"
    for gi, g in enumerate(groups):
        if ended(): status = f"env ended before group {gi}/{len(groups)} (turns_done {env.turns_done()}, stopped {env.stopped()}, time_up {env.time_up()})"; break
        t = g["turn"]
        if t not in base_r: status = f"turn {t} not started before group {gi}"; break
        target = base_r[t] + (g["t"] - base_o.get(t, base_o[0]))
        for _ in range(MAX_WAIT_CELLS):
            w = math.floor(target - 2 * gen_seconds - env.now() + 1e-6)   # wait cell runs at now+gen; the action cell at (wait end)+gen
            if w < 1 or ended(): break
            run_cell(f"SystemApp__wait_for_notification(timeout={w})"); n_wait += 1
        if ended(): status = f"env ended while waiting for group {gi}"; break
        code, pr = group_code(g, var_of, referenced, env_return, perturb); probs += pr
        out, t_exec = run_cell(code); drift.append(round(t_exec - target, 3))
        if out.startswith("Execution failed"): probs.append(f"group {gi} failed: {out[-200:]}")
        if any(tool == SMTU for _, tool, _, _ in g["events"]): base_r.setdefault(t + 1, t_exec)
    v = env.validate()
    rep = {"tid": tid, "config": config, "status": status, "nb_turns": env.nb_turns, "n_groups": len(groups), "n_items": len(items), "n_wait": n_wait,
           "max_abs_drift": max([abs(d) for d in drift], default=0.0), "drift": drift, "problems": probs[:20], "turns_done": env.turns_done(),
           "ended": ended(), "stub_success": v.get("success"), "stub_rationale": (v.get("rationale") or "")[:400], "G": v.get("G"),
           "duration": env.duration, "t_end": round(env.now() - env.start_time, 3), "cells": cells, "build_s": round(time.time() - t0, 1), **info}
    return items, rep


def _build_worker(args):
    tid, seed, gen, ct, pt = args
    try: return tid, *build_one(tid, seed, gen, ct, pt)
    except Exception as e:
        import traceback
        return tid, None, {"tid": tid, "status": f"crash {type(e).__name__}: {str(e)[:200]}", "tb": traceback.format_exc()[-1500:]}


def cmd_build(a):
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor, as_completed
    tasks = json.load(open(a.tasks, encoding="utf-8")); items, reps = {}, {}
    jobs = [(t, a.seed, a.gen_seconds, a.cell_timeout, a.perturb) for t in tasks]
    with ProcessPoolExecutor(max_workers=a.workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        for fut in as_completed([ex.submit(_build_worker, j) for j in jobs]):
            tid, it, rep = fut.result(); reps[tid] = rep
            if it is not None and rep.get("status") == "ok": items[tid] = it
            print(f"  {tid} {rep.get('config')} {rep.get('status')} items={rep.get('n_items')} waits={rep.get('n_wait')} drift={rep.get('max_abs_drift')} "
                  f"stub_success={rep.get('stub_success')} problems={len(rep.get('problems') or [])}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f: json.dump(items, f, indent=1, ensure_ascii=False)
    rp = a.out[:-5] + "_report.json" if a.out.endswith(".json") else a.out + "_report.json"
    with open(rp, "w", encoding="utf-8") as f: json.dump([reps[t] for t in tasks if t in reps], f, indent=1, ensure_ascii=False, default=str)
    ok = [t for t in tasks if t in items]
    print(f"build: {len(ok)}/{len(tasks)} scenarios with items -> {a.out} (report {rp}); max items {max([len(items[t]) for t in ok], default=0)}", flush=True)
    for t in tasks:
        if t not in items: print(f"  SKIP {t}: {reps.get(t, {}).get('status')}", flush=True)


def cmd_pick(a):
    index = json.load(open(os.environ.get("G2_INDEX", "/root/autodl-tmp/cc/gaia2/data/index.json"), encoding="utf-8"))
    pool = json.load(open(a.split, encoding="utf-8")); per = dict((k, int(v)) for k, v in (x.split("=") for x in a.per.split(",")))
    out = []
    for c, n in per.items(): out += [t for t in pool if index[t]["config"] == c][:n]
    with open(a.out, "w", encoding="utf-8") as f: json.dump(out, f)
    print(f"pick: {len(out)} tids {dict(Counter(index[t]['config'] for t in out))} -> {a.out}")


def cmd_report(a):
    R = json.load(open(a.result, encoding="utf-8"))
    reps = {r["tid"]: r for r in json.load(open(a.build[:-5] + "_report.json", encoding="utf-8"))} if a.build else {}
    by = defaultdict(list)
    for i, t in enumerate(R["games"]): by[R["configs"][i]].append(i)
    for c, ix in sorted(by.items(), key=lambda kv: str(kv[0])):
        print(f"{c}: success {sum(R['won'][i] for i in ix)}/{len(ix)}  mean G {sum((R['G'][i] or 0) for i in ix) / len(ix):.2f}")
    print(f"judge hits/misses {R.get('judge_hits')}/{R.get('judge_misses')}")
    for i, t in enumerate(R["games"]):
        if R["won"][i]: continue
        rp = reps.get(t, {})
        print(f"FAIL {t} [{R['configs'][i]}] end={R['end_reason'][i]} steps={R['steps'][i]} G={R['G'][i]} crashed={R['crashed'][i]} "
              f"drift={rp.get('max_abs_drift')} problems={rp.get('problems')}\n   rationale: {(R['rationale'][i] or '')[:700]}"
              + (f"\n   diag: {(R['rationale_diag'][i] or '')[:400]}" if R["rationale_diag"][i] else ""))


def _reexec():
    if os.environ.get("PYTHONHASHSEED") == "0" or os.environ.get("G2_NO_REEXEC") == "1": return
    env = {**os.environ, "PYTHONHASHSEED": "0"}; argv = [sys.executable, os.path.abspath(__file__)] + sys.argv[1:]
    if os.name == "posix": os.execve(sys.executable, argv, env)
    sys.exit(subprocess.call(argv, env=env))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("build"); p.add_argument("--tasks", required=True); p.add_argument("--out", required=True); p.add_argument("--seed", type=int, default=1)
    p.add_argument("--workers", type=int, default=8); p.add_argument("--gen-seconds", type=float, default=float(os.environ.get("G2_GEN_SECONDS", "1.0")))
    p.add_argument("--cell-timeout", type=float, default=float(os.environ.get("G2_CELL_TIMEOUT", "30")))
    p.add_argument("--perturb", choices=["none", "space", "suffix"], default="none", help=f"edit {PERTURB_ARGS} args (exercises the LLM judge; see perturb_text)")
    p = sp.add_parser("pick"); p.add_argument("--per", default="execution=20,search=20,adaptability=4,time=4")
    p.add_argument("--split", default=os.path.join(HERE, "data", "tasks_disc.json")); p.add_argument("--out", required=True)
    p = sp.add_parser("report"); p.add_argument("--result", required=True); p.add_argument("--build", default=None)
    a = ap.parse_args()
    if a.cmd == "build": _reexec(); os.environ["PYTHONHASHSEED"] = "0"; cmd_build(a)
    elif a.cmd == "pick": cmd_pick(a)
    else: cmd_report(a)


if __name__ == "__main__":
    main()
