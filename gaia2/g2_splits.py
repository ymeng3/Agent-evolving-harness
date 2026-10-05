"""Gaia2 scenario index, preflight and frozen splits (GAIA2_ADAPTER_PLAN §2 U5, §4).

 index     : read <data>/<config>/validation-00000-of-00001.parquet for every config, write G2_SCEN_DIR/<tid>.json.gz and
             G2_INDEX = {tid: {config, row_id, scenario_id, universe, tags, nb_turns}} (tid = scenario_id if unique across the
             5 capability configs, else f"{config}__{scenario_id}"); mini/demo rows are indexed only when their scenario_id is
             new, and their overlap with the capability configs (by scenario_id and by data hash) is reported.
 preflight : load every indexed scenario through g2_env.G2Env (stub judge engine, one spawned process per scenario) and
             record ok/err, nb_turns, n_oracle_writes, apps, n_tools, index_chars, tags, duration, first task.
 make      : pool = 5 capability configs minus mini/demo-only rows, duplicate scenarios and preflight failures; within a config
             sort by sha256("g2split:"+tid), then round-robin over universes; disc 60 / val 30 / test rest per config (scaled
             when a config is not 160); tasks_pilot = first 10 of disc per config, tasks_disc_core = first 30.
             Writes tasks_{pilot,disc_core,disc,val,test}.json, instructions_all.json (tid -> first-turn user task, parsed from
             the scenario JSON without ARE) and splits.json.
usage (server, are-env python):
  python gaia2/g2_splits.py index [--data /root/autodl-tmp/cc/gaia2/data]
  python gaia2/g2_splits.py preflight --workers 8 [--out gaia2/data/preflight.json] [--n N]
  python gaia2/g2_splits.py make [--preflight gaia2/data/preflight.json] [--out gaia2/data]"""
import argparse, collections, gzip, hashlib, json, os, re, sys, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
CAP_CONFIGS = ["execution", "search", "adaptability", "time", "ambiguity"]
EXTRA_CONFIGS = ["mini", "demo"]
DATA_DIR = "/root/autodl-tmp/cc/gaia2/data"
SCEN_DIR = os.environ.get("G2_SCEN_DIR", "/root/autodl-tmp/cc/gaia2/scenarios")
INDEX = os.environ.get("G2_INDEX", "/root/autodl-tmp/cc/gaia2/data/index.json")
SEED = "g2split:"
PER_CONFIG = {"disc": 60, "val": 30}  # test = rest; nominal config size 160
SUBSETS = {"pilot": 10, "disc_core": 30}  # taken from the head of disc per config
UNIV_RE = re.compile(r"scenario_universe_(\d+)_")


def universe_of(scenario_id):
    m = UNIV_RE.search(scenario_id)
    return int(m.group(1)) if m else None


def _sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def _write_json(path, obj, indent=None):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(obj, f, indent=indent, ensure_ascii=False)
    os.replace(tmp, path)


def read_scenario(tid, scen_dir=None):
    with gzip.open(os.path.join(scen_dir or SCEN_DIR, tid + ".json.gz"), "rt", encoding="utf-8") as f: return f.read()


# ---------------------------------------------------------------- static scenario parsing (no ARE)
def _is_smtu(e):
    a = e.get("action") or {}
    return e.get("event_type") == "AGENT" and a.get("app") == "AgentUserInterface" and a.get("function") == "send_message_to_user"


def _is_task(e):
    a = e.get("action") or {}
    return a.get("app") == "AgentUserInterface" and a.get("function") == "send_message_to_agent"


def turn_index(events):
    """event_id -> turn (number of send_message_to_user events on the longest dependency path above it), as in
    build_event_id_to_turn_idx / benchmark_scenario; nb_turns = max + 1."""
    by_id = {e["event_id"]: e for e in events}; memo = {}

    def turn(eid, depth=0):
        if eid in memo: return memo[eid]
        deps = [d for d in (by_id[eid].get("dependencies") or []) if d in by_id]
        t = 0
        if deps and depth < 10000:
            t = max(turn(d, depth + 1) for d in deps) + (1 if any(_is_smtu(by_id[d]) for d in deps) else 0)
        memo[eid] = t
        return t
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))
    return {eid: turn(eid) for eid in by_id}


def static_info(scenario_json):
    d = json.loads(scenario_json); ev = d.get("events") or []
    ti = turn_index(ev); nb = (max(ti.values()) + 1) if ti else 1
    tasks = collections.defaultdict(str)
    for e in ev:  # same merge as validation.utils.scenario_utils.extract_tasks (event list order)
        if _is_task(e):
            args = {a.get("name"): a.get("value") for a in (e["action"].get("args") or [])}
            tasks[ti[e["event_id"]]] += str(args.get("content", "")) + "\n"
    oracle = [e for e in ev if e.get("class_name") == "OracleEvent" and e.get("event_type") == "AGENT"]
    defn = (d.get("metadata") or {}).get("definition") or {}
    return {"nb_turns": nb, "tasks": [tasks.get(i, "") for i in range(nb)], "tags": defn.get("tags") or [],
            "n_oracle_events": len(oracle), "n_oracle_smtu": sum(_is_smtu(e) for e in oracle),
            "n_oracle_writes_static": sum((e.get("action") or {}).get("operation_type") == "WRITE" for e in oracle),
            "apps": [a.get("name") for a in (d.get("apps") or [])]}


# ---------------------------------------------------------------- index
def cmd_index(a):
    import pyarrow.parquet as pq
    rows = {}
    for c in CAP_CONFIGS + EXTRA_CONFIGS:
        p = os.path.join(a.data, c, "validation-00000-of-00001.parquet")
        if not os.path.exists(p): print(f"[index] missing {p}"); continue
        rows[c] = pq.read_table(p).to_pylist()
    print("[index] rows per config: " + ", ".join(f"{c}={len(r)}" for c, r in rows.items()))
    sid_cfgs = collections.defaultdict(list)
    for c in CAP_CONFIGS:
        for r in rows.get(c, []): sid_cfgs[r["scenario_id"]].append(c)
    dup = {s: cs for s, cs in sid_cfgs.items() if len(cs) > 1}
    unique = not dup
    print(f"[index] capability scenario_ids: {sum(len(v) for v in sid_cfgs.values())} rows, {len(sid_cfgs)} distinct; "
          f"unique across configs: {unique}" + ("" if unique else f" ({len(dup)} repeated, e.g. {list(dup.items())[:3]})"))
    if not unique: print("[index] tid = f'{config}__{scenario_id}' for capability configs")
    split_vals = collections.Counter(r.get("split") for rs in rows.values() for r in rs)
    print(f"[index] split column values: {dict(split_vals)}")

    os.makedirs(a.scen_dir, exist_ok=True)
    index, data_hash = {}, {}
    rep = {"rows": {c: len(r) for c, r in rows.items()}, "tid_unique": unique, "repeated_scenario_ids": dup}
    for c in CAP_CONFIGS:
        for r in rows.get(c, []):
            sid = r["scenario_id"]; tid = sid if unique else f"{c}__{sid}"
            assert "/" not in tid and ":" not in tid, tid
            assert tid not in index, f"tid collision {tid}"
            si = static_info(r["data"]); h = _sha(r["data"])
            index[tid] = {"config": c, "row_id": r["id"], "scenario_id": sid, "universe": universe_of(sid),
                          "tags": si["tags"], "nb_turns": si["nb_turns"], "data_sha": h}
            data_hash.setdefault(h, []).append(tid)
            with gzip.open(os.path.join(a.scen_dir, tid + ".json.gz"), "wt", encoding="utf-8") as f: f.write(r["data"])
    dup_data = {h: ts for h, ts in data_hash.items() if len(ts) > 1}
    print(f"[index] identical scenario data among capability tids: {len(dup_data)} groups" +
          ("" if not dup_data else f" e.g. {list(dup_data.values())[:3]}"))
    rep["duplicate_data_groups"] = list(dup_data.values())

    by_sid = {v["scenario_id"]: t for t, v in index.items()}
    for c in EXTRA_CONFIGS:
        same_sid = same_data = diff_data = new = 0; cats = collections.Counter(); diff_ex = []
        for r in rows.get(c, []):
            sid = r["scenario_id"]; h = _sha(r["data"]); cats[r.get("category") or "-"] += 1
            hit = by_sid.get(sid) if unique else next((t for t, v in index.items() if v["scenario_id"] == sid), None)
            if hit is not None:
                same_sid += 1
                if index[hit]["data_sha"] == h: same_data += 1
                else: diff_data += 1; diff_ex.append(sid)
                index[hit].setdefault("also_in", []).append(c)
                continue
            if h in data_hash: same_data += 1; index[data_hash[h][0]].setdefault("also_in", []).append(c); continue
            new += 1; tid = sid if sid not in index else f"{c}__{sid}"
            si = static_info(r["data"])
            index[tid] = {"config": c, "row_id": r["id"], "scenario_id": sid, "universe": universe_of(sid),
                          "tags": si["tags"], "nb_turns": si["nb_turns"], "data_sha": h, "category": r.get("category")}
            with gzip.open(os.path.join(a.scen_dir, tid + ".json.gz"), "wt", encoding="utf-8") as f: f.write(r["data"])
        print(f"[index] {c}: {len(rows.get(c, []))} rows; scenario_id in capability configs {same_sid} "
              f"(identical data {same_data}, different data {diff_data}{' e.g. ' + str(diff_ex[:3]) if diff_ex else ''}); "
              f"new {new}; category {dict(cats)}")
        rep[c] = {"same_scenario_id": same_sid, "identical_data": same_data, "different_data": diff_data, "new": new,
                  "category": dict(cats)}
    for c in CAP_CONFIGS:
        ts = [v for v in index.values() if v["config"] == c]
        nt = collections.Counter(v["nb_turns"] for v in ts); un = collections.Counter(v["universe"] for v in ts)
        tg = collections.Counter(tuple(v["tags"]) for v in ts)
        print(f"[index] {c}: {len(ts)} tids, {len(un)} universes (min/max per universe {min(un.values())}/{max(un.values())}), "
              f"nb_turns {dict(sorted(nt.items()))}, tags {dict(tg)}")
    _write_json(a.index, index)
    _write_json(os.path.join(os.path.dirname(os.path.abspath(a.index)), "index_report.json"), rep, indent=1)
    print(f"[index] wrote {len(index)} tids -> {a.index}; scenarios -> {a.scen_dir}")


# ---------------------------------------------------------------- preflight
def _stub_engine():
    try:
        from are.simulation.agents.llm.llm_engine import LLMEngine
    except Exception:
        LLMEngine = object

    class StubJudgeEngine(LLMEngine):
        """Never contacted during construction; answers [[Success]] if validate() reaches an LLM check."""
        def __init__(self):
            if LLMEngine is not object: super().__init__("stub-judge")
            self.calls = 0

        def __call__(self, messages, stop_sequences=[], **kw): return self.chat_completion(messages, stop_sequences, **kw)

        def chat_completion(self, messages, stop_sequences=[], **kw):
            self.calls += 1
            return "[[Success]]", {}
    return StubJudgeEngine()


def _preflight_one(tid, gen_seconds):
    t0 = time.time(); rec = {"tid": tid, "ok": False}
    try:
        sys.path.insert(0, HERE)
        import g2_env
        g2_env.install_determinism(); g2_env.begin_episode(tid, 0)
        config, sj = g2_env.load_scenario_json(tid)
        si = static_info(sj)
        rec.update(config=config, tags=si["tags"], nb_turns_static=si["nb_turns"],
                   n_oracle_writes_static=si["n_oracle_writes_static"], n_oracle_events=si["n_oracle_events"])
        eng = _stub_engine()
        env = g2_env.G2Env(sj, eng, gen_seconds=gen_seconds, tid=tid, seed=0)
        tools = env.tools()
        rec.update(nb_turns=env.nb_turns, duration=env.duration, start_time=env.start_time,
                   n_tools=len(tools), apps=sorted({t._public_name.split("__")[0] for t in tools}),
                   has_additional_system_prompt=bool(env.additional_system_prompt))
        try:
            import g2_exec
            rec["index_chars"] = len(g2_exec.format_tool_index(tools))
        except Exception as e:
            rec["index_chars"] = None; rec["index_err"] = f"{type(e).__name__}: {e}"[:300]
        rec["first_task"] = env.first_task()
        rec["first_task_static_match"] = rec["first_task"].rstrip("\n") == si["tasks"][0].rstrip("\n")
        rec["nb_turns_static_match"] = env.nb_turns == si["nb_turns"]
        try:
            v = env.validate()
            rec.update(n_oracle_writes=v.get("n_oracle_writes"), oracle_counts=v.get("oracle_counts"))
        except Exception as e:
            rec["validate_err"] = f"{type(e).__name__}: {e}"[:300]
        rec["judge_calls"] = eng.calls; rec["ok"] = True
    except Exception as e:
        rec["err"] = f"{type(e).__name__}: {e}"[:500]; rec["tb"] = traceback.format_exc()[-2000:]
    rec["wall_s"] = round(time.time() - t0, 2)
    return rec


def cmd_preflight(a):
    import concurrent.futures as cf, multiprocessing as mp
    os.environ["PYTHONHASHSEED"] = "0"  # inherited by spawned workers (read at interpreter start)
    os.environ.setdefault("G2_SCEN_DIR", a.scen_dir); os.environ.setdefault("G2_INDEX", a.index)
    index = json.load(open(a.index, encoding="utf-8"))
    tids = sorted(t for t, v in index.items() if a.all or v["config"] in CAP_CONFIGS)
    if a.n: tids = tids[:a.n]
    done = {}
    if os.path.exists(a.out) and not a.fresh:
        done = {r["tid"]: r for r in json.load(open(a.out, encoding="utf-8")) if r.get("ok")}
        print(f"[preflight] resuming: {len(done)} ok records kept")
    todo = [t for t in tids if t not in done]; recs = dict(done); t0 = time.time()
    ex = cf.ProcessPoolExecutor(a.workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1)
    futs = {ex.submit(_preflight_one, t, a.gen_seconds): t for t in todo}
    try:
        for i, f in enumerate(cf.as_completed(futs), 1):
            t = futs[f]
            try: r = f.result()
            except Exception as e: r = {"tid": t, "ok": False, "err": f"worker: {type(e).__name__}: {e}"[:500]}
            recs[t] = r
            if not r["ok"]: print(f"[preflight] ERR {t}: {r.get('err')}")
            if i % 25 == 0 or i == len(todo):
                print(f"[preflight] {i}/{len(todo)} done, {sum(not x['ok'] for x in recs.values())} err, {time.time() - t0:.0f}s")
                _write_json(a.out, [recs[x] for x in sorted(recs)], indent=1)
    finally:
        ex.shutdown(cancel_futures=True)
    out = [recs[x] for x in sorted(recs)]; _write_json(a.out, out, indent=1)
    ok = [r for r in out if r["ok"]]
    print(f"[preflight] {len(ok)}/{len(out)} ok -> {a.out}")
    for c in CAP_CONFIGS:
        rs = [r for r in ok if r.get("config") == c]
        if not rs: continue
        ic = sorted(r["index_chars"] for r in rs if r.get("index_chars"))
        print(f"[preflight] {c}: ok {len(rs)}, nb_turns {dict(collections.Counter(r['nb_turns'] for r in rs))}, "
              f"n_tools {min(r['n_tools'] for r in rs)}-{max(r['n_tools'] for r in rs)}"
              + (f", index_chars median {ic[len(ic) // 2]} p95 {ic[int(0.95 * (len(ic) - 1))]}" if ic else ""))


# ---------------------------------------------------------------- make
def order_config(tids, index):
    """sha256("g2split:"+tid) order, then round-robin over universes (universe order = rank of its first member)."""
    tids = sorted(tids, key=lambda t: _sha(SEED + t)); groups = {}
    for t in tids: groups.setdefault(index[t]["universe"], []).append(t)
    out, k = [], 0
    while len(out) < len(tids):
        for g in groups.values():
            if k < len(g): out.append(g[k])
        k += 1
    return out


def cmd_make(a):
    index = json.load(open(a.index, encoding="utf-8")); excl = collections.Counter()
    pool = {c: [] for c in CAP_CONFIGS}; seen_data = set()
    bad = set()
    if a.preflight:
        pf = json.load(open(a.preflight, encoding="utf-8")); bad = {r["tid"] for r in pf if not r.get("ok")}
        missing = {t for t, v in index.items() if v["config"] in CAP_CONFIGS} - {r["tid"] for r in pf}
        if missing: print(f"[make] WARNING {len(missing)} capability tids absent from preflight file; treated as failures"); bad |= missing
    for t in sorted(index, key=lambda t: (index[t]["config"], _sha(SEED + t))):
        v = index[t]
        if v["config"] not in CAP_CONFIGS: excl["mini/demo"] += 1; continue
        if v["data_sha"] in seen_data: excl["duplicate"] += 1; continue
        seen_data.add(v["data_sha"])
        if t in bad: excl["preflight_fail"] += 1; continue
        pool[v["config"]].append(t)
    splits = {s: [] for s in ["pilot", "disc_core", "disc", "val", "test"]}; per = {}
    for c in CAP_CONFIGS:
        o = order_config(pool[c], index); n = len(o)
        nd = round(PER_CONFIG["disc"] * n / 160); nv = round(PER_CONFIG["val"] * n / 160)
        np_, nc = round(SUBSETS["pilot"] * n / 160), round(SUBSETS["disc_core"] * n / 160)
        disc, val, test = o[:nd], o[nd:nd + nv], o[nd + nv:]
        splits["disc"] += disc; splits["val"] += val; splits["test"] += test
        splits["pilot"] += disc[:np_]; splits["disc_core"] += disc[:nc]
        per[c] = {"pool": n, "disc": len(disc), "val": len(val), "test": len(test), "pilot": len(disc[:np_]),
                  "disc_core": len(disc[:nc]), "universes": {s: len({index[t]["universe"] for t in x})
                                                             for s, x in [("disc", disc), ("val", val), ("test", test)]}}
    a_d, a_v, a_t = set(splits["disc"]), set(splits["val"]), set(splits["test"])
    assert not (a_d & a_v or a_d & a_t or a_v & a_t), "splits overlap"
    assert set(splits["pilot"]) <= set(splits["disc_core"]) <= a_d
    for s, x in splits.items(): assert len(x) == len(set(x)), f"duplicates in {s}"

    instr, missing = {}, []
    for t in sorted(index):
        try:
            tasks = static_info(read_scenario(t, a.scen_dir))["tasks"]
            instr[t] = tasks[0].rstrip("\n") if tasks and tasks[0].strip() else ""
        except Exception as e:
            instr[t] = ""; print(f"[make] instr parse failed {t}: {e}")
        if not instr[t]: missing.append(t)
    split_tids = a_d | a_v | a_t
    miss_split = [t for t in split_tids if not instr.get(t)]
    assert not miss_split, f"no first-turn instruction for {len(miss_split)} split tids, e.g. {miss_split[:5]}"

    os.makedirs(a.out, exist_ok=True)
    for s, x in splits.items(): _write_json(os.path.join(a.out, f"tasks_{s}.json"), x)
    _write_json(os.path.join(a.out, "instructions_all.json"), instr, indent=1)
    meta = {"rule": "pool = validation configs " + ",".join(CAP_CONFIGS) + " (mini/demo excluded; duplicate scenario data "
                    "dropped, first by (config, hash) order kept; preflight failures excluded when --preflight is given); "
                    "within a config sort by sha256(seed+tid), then round-robin over universes (scenario_universe_(\\d+)_, "
                    "universe order = hash rank of its first member); disc = first round(60n/160), val = next round(30n/160), "
                    "test = rest; pilot = first round(10n/160) of disc, disc_core = first round(30n/160) of disc",
            "seed": SEED, "preflight": a.preflight, "index": os.path.abspath(a.index),
            "counts": {s: len(x) for s, x in splits.items()}, "per_config": per, "excluded": dict(excl),
            "instructions_missing": missing,
            "made": time.strftime("%Y-%m-%d %H:%M:%S")}
    _write_json(os.path.join(a.out, "splits.json"), meta, indent=1)
    print(f"[make] excluded {dict(excl)}")
    for c, p in per.items(): print(f"[make] {c}: {p}")
    print(f"[make] counts {meta['counts']}; instructions {len(instr)} ({len(missing)} empty, none in splits) -> {a.out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ["index", "preflight", "make"]:
        p = sp.add_parser(name)
        p.add_argument("--scen-dir", default=SCEN_DIR); p.add_argument("--index", default=INDEX)
        if name == "index": p.add_argument("--data", default=DATA_DIR)
        if name == "preflight":
            p.add_argument("--workers", type=int, default=8); p.add_argument("--n", type=int, default=0)
            p.add_argument("--gen-seconds", type=float, default=float(os.environ.get("G2_GEN_SECONDS", "1.0")))
            p.add_argument("--out", default=os.path.join(HERE, "data", "preflight.json"))
            p.add_argument("--all", action="store_true", help="also mini/demo-only tids")
            p.add_argument("--fresh", action="store_true", help="ignore an existing --out file")
        if name == "make":
            p.add_argument("--preflight", default=None); p.add_argument("--out", default=os.path.join(HERE, "data"))
    a = ap.parse_args()
    {"index": cmd_index, "preflight": cmd_preflight, "make": cmd_make}[a.cmd](a)


if __name__ == "__main__":
    main()
