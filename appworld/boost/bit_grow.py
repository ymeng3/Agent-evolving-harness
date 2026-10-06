"""Depth-wise intervention-tree growth (docs/design/BIT_DEPTHWISE.md): split the node of an admitted tree (its branch-at-fire states) into a
kept child (parent AND child detector -> intervention) and its complement (-> no intervention), XGBoost style with unit hessians.
nodes     The node of a parent tree = its branch states pooled over builds (bit_lowrank.collect). Per state: eid, task, k, kind, note,
          logged_won, cand wins/n, none wins/n, d_s = cand_rate - none_rate, group (helped d>0 / harmed d<0 / neutral d=0), a reference to
          the logged prefix (eid, k, prefix length) and to cand / none continuations that won / lost (result file, tag, tid). Node stats.
propose   One hindsight self-proposer call (same backbone, proposer.chat; BOOST_MOCK=1 = offline mock) shown the node's contrast: helped
          vs harmed / neutral states (prefix, pending cell, the continuation under the intervention), the parent detector + note. It
          writes k CHILD detectors over the same view; each is compiled as one full spec whose detect = parent_detect(view) AND
          child_detect(view) (both nested inside one detect; kind / cls of the parent; the note may be refined). Self-check by offline
          replay of the node's episodes: the child must fire at the parent's step k on >= 1 helped state and must NOT on >= 1 harmed state
          (d <= 0 states if the node has no harmed one); failures are fed back, <= 2 retries. JSONL like bit_propose.
evaluate  In-node partition from the EXISTING branch data: kept = the child fires at the state's step k (it can only fire at k or later).
          Gain = (sum_L d)^2/(|L|+lam) + (sum_R d)^2/(|R|+lam) - (sum_S d)^2/(|S|+lam) - gamma; kept-leaf P(a>0) (independent Beta per
          state and arm, = bit_branch.post_p_pos) and the pooled rank-1 posterior (bit_lowrank); value removed by dropping the complement
          = -sum_R d. Recommends the best child if Gain > gamma (--spec-out writes its spec).
heldout   Branch-at-fire jobs for the refined tree on states NOT in the node: the base logs (incl. extra active-sampling seeds) minus the
          node's episodes (optionally all episodes of the node's tasks) are written to temporary filtered copies and bit_branch.build is
          called on them with a temporary screen.json + --force-cid. Same flags as bit_branch build (--base-specs, --harness-cmd, ...).
usage (in appworld/):
  python boost/bit_grow.py nodes --builds bit/R0/branch_P2 --results results --runs results/A.json,results/B.json --instr I --cid P2_c13_1
                                 --out bit/G1/node.json
  python boost/bit_grow.py propose --node bit/G1/node.json --out bit/G1/cands_G1.jsonl --run-id G1 [--k 3 --parent-spec P.json --dry-run]
  python boost/bit_grow.py evaluate --node bit/G1/node.json --cands bit/G1/cands_G1.jsonl [--lam 1 --gamma 0 --specs extra.json
                                    --spec-out bit/G1/child.json --out bit/G1/eval.json]
  python boost/bit_grow.py heldout --child-spec bit/G1/child.json --runs <base logs incl. extra seeds> --instr I --exclude-eids bit/G1/node.json
                                   --out bit/G1/heldout --round G1H --env-file bit/R0/base_env.txt [--reps 2 --base-specs ... --harness-cmd ...]
  then: python boost/bit_branch.py readout --build bit/G1/heldout --results results --rule posterior   (and bit_lowrank.py --builds bit/G1/heldout)
--runs / --instr / --results of propose and evaluate default to the ones recorded in node.json."""
import argparse, ast, collections, json, os, re, shutil, sys, tempfile, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); AW = os.path.dirname(HERE)
if HERE not in sys.path: sys.path.insert(0, HERE)
import bit_rubric as R   # noqa: E402
from bit_common import load_episodes   # noqa: E402

MAX_RETRIES = 2; PREFIX_FULL = 6; CODE_CHARS = 300; OUT_CHARS = 150; PENDING_CHARS = 600; CONT_STEPS = 10


# ---------------------------------------------------------------- shared
def _max_steps(eps):
    return max((e.get("max_steps") or 30 for e in eps), default=30)


def _load_eps(runs, instr):
    return {e["eid"]: e for e in load_episodes(runs, instr) if not e["crashed"]}


def _prefix_len(ep, k):
    return next((i for i, s in enumerate(ep["steps"]) if s["k"] == k), None)


def split_gain(d, kept, lam=1.0, gamma=0.0):
    """XGBoost split gain with g = -d, h = 1: (sum_L d)^2/(|L|+lam) + (sum_R d)^2/(|R|+lam) - (sum_S d)^2/(|S|+lam) - gamma."""
    d = np.asarray(d, float); m = np.asarray(kept, bool); t = lambda x: float(x.sum()) ** 2 / (len(x) + lam)
    return t(d[m]) + t(d[~m]) - t(d) - gamma


def _rename_detect(src, name):
    det = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "detect"][0]
    det.name = name; return ast.unparse(det)


def combine_detect(parent_src, child_src, refined):
    """one def detect(view) = parent AND child, both nested. The parent's return value (True or its own note string) is kept unless the
    note is refined (then True -> the refined NOTE). The child gets a copy of view, so it cannot change what the parent saw."""
    ind = lambda s: "".join("    " + l + "\n" for l in s.splitlines())
    return ("def detect(view):\n" + ind(_rename_detect(parent_src, "_bit_parent")) + ind(_rename_detect(child_src, "_bit_child"))
            + "    _bit_p = _bit_parent(view)\n    if not _bit_p:\n        return False\n"
            + "    if not _bit_child(dict(view, cells=[dict(c) for c in view['cells']])):\n        return False\n"
            + ("    return True\n" if refined else "    return _bit_p\n"))


def child_spec(parent, child, cid=None):
    """full spec of the refined leaf: kind / cls of the parent; note = the child's refined NOTE if any, else the parent's."""
    R.validate_spec({"name": child.get("name") or "child", "kind": parent["kind"], "cls": parent["cls"], "hypothesis": child.get("hypothesis") or "child",
                     "note": parent["note"], "detect_src": child.get("detect_src") or ""})   # child detector alone: same rules as any detect
    refined = bool((child.get("note") or "").strip()) and child["note"].strip() != parent["note"].strip()
    sp = {"name": child["name"], "kind": parent["kind"], "cls": parent["cls"],
          "hypothesis": (parent.get("hypothesis") or "").strip() + " | child split: " + (child.get("hypothesis") or "").strip(),
          "note": child["note"].strip() if refined else parent["note"], "detect_src": combine_detect(parent["detect_src"], child["detect_src"], refined),
          "origin": {"cid": cid, "parent": parent.get("name"), "parent_cid": (parent.get("origin") or {}).get("cid"), "child_src": child["detect_src"],
                     "refined_note": refined}}
    R.validate_spec(sp); return sp


def fires_at_k(spec, states, eps_by, max_steps, timeout):
    """simulate spec on the node's episodes -> {sid: {"kept": fires at the state's k, "k_fire", "hook_errors"}} (kept None = episode missing)."""
    src = R.compile_patch([spec], max_steps); eids = sorted({s["eid"] for s in states if s["eid"] in eps_by})
    res = R.simulate(src, [eps_by[e] for e in eids], timeout_s=timeout); out = {}
    for s in states:
        r = res.get(s["eid"])
        if r is None: out[s["sid"]] = {"kept": None, "k_fire": None, "hook_errors": None}; continue
        f = r["fires"]; out[s["sid"]] = {"kept": bool(f) and f[0]["k"] == s["k"], "k_fire": f[0]["k"] if f else None, "hook_errors": r["hook_errors"]}
    return src, out


# ---------------------------------------------------------------- nodes
def cmd_nodes(a):
    import bit_lowrank as LR, bit_branch as BB
    builds = [b for b in a.builds.split(",") if b]
    data = LR.collect(builds, a.results).get(a.cid) or {}
    if not data: sys.exit(f"no branch results for {a.cid} in {builds} / {a.results}")
    eps_by = _load_eps(a.runs, a.instr); spec = None; meta_all = {}; refs = collections.defaultdict(dict)
    for b in builds:
        man = json.load(open(os.path.join(b, "manifest.json"), encoding="utf-8"))
        for c in man["cands"]:
            if c["cid"] != a.cid: continue
            spec = spec or c.get("spec")
            for dd in c["dirs"]:
                meta = json.load(open(os.path.join(b, dd["dir"], "meta.json"), encoding="utf-8"))
                for t, m in meta.items(): meta_all.setdefault((dd["seed"], t), m)
                for j in man["jobs"]:
                    if j["cid"] != a.cid or j["dir"] != dd["dir"]: continue
                    fn = f"{j['tag']}_seed{j['seed']}.json"; r = BB.load_result(os.path.join(a.results, fn))
                    for t, (w, G, tr) in (r or {}).items():
                        if t in meta:
                            refs[(dd["seed"], t)].setdefault(f"{j['arm']}_{'won' if w else 'lost'}", {
                                "file": fn, "tag": j["tag"], "seed": j["seed"], "tid": t, "arm": j["arm"], "rep": j["rep"], "build": b,
                                "dir": dd["dir"], "won": bool(w), "G": G, "n_steps": len(tr)})
    if a.parent_spec: spec = json.load(open(a.parent_spec, encoding="utf-8"))
    states, missing = [], []
    for j, (key, st) in enumerate(sorted(data.items())):
        if st["cn"] == 0 or st["nn"] == 0: missing.append(list(key)); continue
        m = meta_all.get(key, {}); ep = eps_by.get(st["eid"]); i = _prefix_len(ep, st["k"]) if ep else None
        cr, nr = st["cw"] / st["cn"], st["nw"] / st["nn"]; d = cr - nr
        states.append({"sid": f"S{len(states) + 1:02d}", "seed": key[0], "task": key[1], "eid": st["eid"], "k": st["k"], "kind": m.get("kind"),
                       "note": m.get("note"), "logged_won": bool(st["logged_won"]), "instr": ep["instr"] if ep else None,
                       "cw": st["cw"], "cn": st["cn"], "nw": st["nw"], "nn": st["nn"], "cand_rate": cr, "none_rate": nr, "d": d,
                       "group": "helped" if d > 0 else "harmed" if d < 0 else "neutral",
                       "prefix": {"eid": st["eid"], "k": st["k"], "n_prefix": i, "in_runs": ep is not None}, "refs": refs.get(key, {})})
    node = {"cid": a.cid, "builds": builds, "results": a.results, "runs": a.runs, "instr": a.instr, "parent_spec": spec,
            "states": states, "missing": missing, "stats": node_stats(states, a.lam)}
    if os.path.dirname(a.out): os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(node, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    s = node["stats"]
    print(f"node {a.cid}: {s['n']} states ({len(missing)} without both arms), sum d = {s['sum_d']:+.2f}, mean d = {s['mean_d']:+.3f}, "
          f"helped {s['n_helped']}, harmed {s['n_harmed']} ({s['n_harmed_logged_won']} logged won), neutral {s['n_neutral']}, "
          f"P(a>0) = {s['p_pos']:.3f}, split eligible: {s['split_eligible']} -> {a.out}")
    for x in states:
        print(f"  {x['sid']} s{x['seed']} {x['task']:12s} k={x['k']:<3d} logged={'won ' if x['logged_won'] else 'lost'} cand {x['cw']}/{x['cn']} "
              f"none {x['nw']}/{x['nn']} d={x['d']:+.2f} {x['group']:8s} refs={sorted(x['refs'])}{'' if x['prefix']['in_runs'] else ' (eid not in --runs!)'}")
    if not spec: print("  ! no parent spec in the manifests: pass --parent-spec")


def node_stats(states, lam=1.0):
    import bit_branch as BB
    d = np.array([s["d"] for s in states], float); n = len(d)
    harmed = [s for s in states if s["d"] < 0]
    return {"n": n, "sum_d": float(d.sum()), "mean_d": float(d.mean()) if n else 0.0, "sd_d": float(d.std()) if n else 0.0,
            "n_helped": sum(s["d"] > 0 for s in states), "n_harmed": len(harmed), "n_neutral": sum(s["d"] == 0 for s in states),
            "n_harmed_logged_won": sum(s["logged_won"] for s in harmed), "n_logged_won": sum(s["logged_won"] for s in states),
            "root_score": float(d.sum()) ** 2 / (n + lam) if n else 0.0, "p_pos": BB.post_p_pos(states) or 0.0,
            "split_eligible": bool(n >= 4 and (harmed or (n and d.std() > 0.3))),
            "harmed": [s["sid"] for s in harmed], "helped": [s["sid"] for s in states if s["d"] > 0]}


# ---------------------------------------------------------------- propose: prompt
def _clip(s, n):
    s = s or ""
    return s if len(s) <= n else s[:n] + f" ...[+{len(s) - n} chars]"


def _one_line(s, n=100):
    s = " | ".join(l.strip() for l in (s or "").splitlines() if l.strip())
    return _clip(s, n)


def _ind(s, pre="      "):
    return "\n".join(pre + l for l in (s or "").splitlines()) or pre


def fmt_prefix(ep, i):
    """steps[:i] compactly: the last PREFIX_FULL steps with code / out, earlier ones as one line each."""
    L = []
    for j, s in enumerate(ep["steps"][:i]):
        if s["no_exec"]: L.append(f"  [step {s['k']}] (no code executed; not in view['cells'])"); continue
        if j < i - PREFIX_FULL: L.append(f"  [step {s['k']}] {_one_line(s['code'])}" + ("  -> ERROR" if s["err"] else "")); continue
        L.append(f"  [step {s['k']}] code:\n{_ind(_clip(s['code'], CODE_CHARS))}\n    -> out{' (ERROR)' if s['err'] else ''}:\n{_ind(s['out'][:OUT_CHARS])}")
    return "\n".join(L) or "  (empty prefix: the rule fired at the first step)"


def fmt_continuation(tr, i, kind, ref):
    """the branch continuation from the fire step on (replayed prefix skipped)."""
    L = []
    if kind == "block_once" and len(tr) > i and tr[i].get("replayed"):
        L.append(f"  [step {tr[i].get('step', i)}] the pending cell was BLOCKED; the agent saw: {_clip(tr[i].get('out'), 200)}"); start = i + 1
    else: start = i
    live = [s for s in tr[start:] if not s.get("replayed")]
    for s in live[:CONT_STEPS]:
        code = s.get("code") or ""
        if not code: L.append(f"  [step {s.get('step')}] (no code executed)"); continue
        out = s.get("out") or ""
        L.append(f"  [step {s.get('step')}] code:\n{_ind(_clip(code, CODE_CHARS))}\n    -> out{' (ERROR)' if out.startswith('Execution failed') else ''}:\n{_ind(out[:OUT_CHARS])}")
    if len(live) > CONT_STEPS: L.append(f"  ... {len(live) - CONT_STEPS} more step(s)")
    G = ref.get("G")
    L.append(f"  => this continuation {'SUCCEEDED' if ref.get('won') else 'FAILED'}" + (f" (G = {G:.2f})" if G is not None else ""))
    return "\n".join(L)


def _harness_text(bench, max_steps):
    if bench == "gaia2":
        import bit_propose as BP
        return BP._harness_g2(max_steps)
    return ("## 1. The harness\n"
            "An LLM agent solves AppWorld tasks: everyday tasks over simulated apps (amazon, gmail, venmo, spotify, phone, file_system, ...) that "
            "it reaches from python through `apis.<app>.<api>(...)`. At each step the agent writes ONE python code cell; the harness executes it "
            f"and shows the output. The budget is {max_steps} steps (step indices 0..{max_steps - 1}). The episode ends when the agent calls "
            "`apis.supervisor.complete_task(...)` or when the budget runs out; the environment's tests then check the final state of the apps.\n"
            "The harness has RULES: a detector `detect(view)` plus a NOTE. When the detector fires during an episode, the harness intervenes "
            "once (shows the note, or blocks the pending cell and shows the note).")


def _state_block(s, eps_by, results, res_cache):
    import bit_branch as BB
    ep = eps_by.get(s["eid"]); i = s["prefix"]["n_prefix"]
    H = [f"### {s['sid']} ({s['group'].upper()}: d = {s['d']:+.2f}; with the rule {s['cw']}/{s['cn']} won, without it {s['nw']}/{s['nn']} won; "
         f"the logged run {'SUCCEEDED' if s['logged_won'] else 'FAILED'} without any intervention)",
         f"Task: {s.get('instr') or (ep or {}).get('instr') or '?'}", f"The rule fired at step {s['k']}."]
    if ep is None or i is None: H.append("(the logged prefix is not available)"); return "\n".join(H)
    H.append("Prefix (executed before the rule fired):\n" + fmt_prefix(ep, i))
    if s["kind"] == "block_once" and i < len(ep["steps"]):
        H.append("Pending cell (the cell the rule blocked; view['pending'] at the firing step):\n" + _ind(_clip(ep["steps"][i]["code"], PENDING_CHARS), "    "))
    else: H.append("(note rule: fired before the LLM call of this step; view['pending'] is None)")
    want = ["cand_won", "cand_lost"] if s["group"] == "helped" else ["cand_lost", "cand_won"]
    ref = next((s["refs"][x] for x in want if x in s["refs"]), None)
    if ref:
        p = os.path.join(results, ref["file"])
        if p not in res_cache: res_cache[p] = BB.load_result(p) or {}
        r = res_cache[p].get(ref["tid"])
        if r: H.append("Continuation WITH the rule (one branch run):\n" + fmt_continuation(r[2], i, s["kind"], ref))
    return "\n".join(H)


def build_prompt(node, parent, eps_by, results, k=3, max_steps=30, bench="appworld", max_show=8):
    import bit_propose as BP
    st = node["states"]; res_cache = {}
    P = [_harness_text(bench, max_steps)]
    P.append("## 2. What a detector sees (hard rule)\n`detect` receives only this `view` (exact schema):\n```python\n"
             + BP.VIEW_SCHEMA.replace('"max_steps": 30', f'"max_steps": {max_steps}') + "\n```\n"
             "It must be decidable from the prefix observed so far: it cannot see the agent's reasoning, outputs beyond 200 characters, the task id, "
             "the outcome, or anything that happens later. Pure function of view; imports only inside detect and only from re, json, math, random, "
             "collections, itertools, string; open/exec/eval/getattr/setattr/globals and dunder names are forbidden.")
    kd = ("block_once: detect is called after the agent wrote its cell and before it is executed (view['pending'] = that code); the first time it "
          "fires, the cell is NOT executed, the agent sees \"[harness note] Your cell was NOT executed. <note>\" and writes the step again."
          if parent["kind"] == "block_once" else
          "note: detect is called before each step's LLM call (view['pending'] is None); the first time it fires, \"[harness note] <note>\" is "
          "appended to that step's prompt.")
    P.append(f"## 3. The current rule (the parent)\nNAME: {parent['name']}\nKIND: {kd}\nHYPOTHESIS: {parent.get('hypothesis', '')}\n"
             f"NOTE: {parent['note']}\n```python\n{parent['detect_src'].rstrip()}\n```")
    s = node["stats"]
    groups = [("helped", "HELPED states (the rule raised the success rate)"), ("harmed", "HARMED states (the rule lowered the success rate)"),
              ("neutral", "NEUTRAL states (no measurable effect)")]
    C = [f"## 4. Where the rule fired, and what it did there (privileged hindsight)\nThe rule fired on {s['n']} states of past episodes. At each "
         "state the episode was re-run from the same prefix several times WITH the intervention and WITHOUT it; d = success rate with minus "
         f"success rate without. Sum of d = {s['sum_d']:+.2f}: {s['n_helped']} helped, {s['n_harmed']} harmed, {s['n_neutral']} neutral."]
    for g, title in groups:
        xs = sorted([x for x in st if x["group"] == g], key=lambda x: -abs(x["d"]))
        if not xs: continue
        C.append(f"## {title}: {len(xs)}" + (f" (the {max_show} with the largest |d| are shown)" if len(xs) > max_show else ""))
        C += [_state_block(x, eps_by, results, res_cache) for x in xs[:max_show]]
    P.append("\n\n".join(C))
    tgt = "harmed" if s["n_harmed"] else "harmed or neutral"
    P.append("## 5. What to write\n"
             f"First, in at most 3 sentences: what distinguishes the helped states from the {tgt} states, as visible in the view at the firing step.\n"
             f"Then write {k} different CHILD detectors. The refined rule fires where the parent fires AND the child returns true; elsewhere the "
             "harness does not intervene. Each child must:\n"
             "- return true on the helped states and false on the " + tgt + " states, evaluated on the view at the parent's firing step (same "
             "view schema; for block_once view['pending'] is the cell the parent blocked);\n"
             "- be GENERAL: key on the structure of the task wording, the code and the outputs; no task-specific names, ids, numbers or long literals;\n"
             "- optionally refine the NOTE of the kept intervention (20..600 chars, factual, actionable, no solution of any task). Write "
             "NOTE = None to keep the parent's note.\n"
             "Each child is checked automatically by replaying the episodes above: parent AND child must fire at the firing step on at least one "
             f"helped state and must NOT fire there on at least one {tgt} state. If a check fails you get the reason back.")
    P.append("## 6. Output format\n<what distinguishes helped from harmed, at most 3 sentences>\n\nthen, for each child:\n"
             "NAME: <snake_case, <= 40 chars>\nHYPOTHESIS: <one or two sentences: the sub-population the parent should leave alone, and why>\n"
             "```python\nNOTE = None\ndef detect(view):\n    ...\n```\n"
             "Only NOTE and `def detect(view):` may appear at the top level of the block (detect is the CHILD only; the harness adds the parent); "
             "put imports and helpers inside detect.")
    return "\n\n".join(P)


# ---------------------------------------------------------------- propose: calls
def ask(messages, max_tokens):
    import bit_propose as BP
    if os.environ.get("BOOST_MOCK") == "1": return _mock_chat(messages), [{"in": 0, "out": 0, "finish": "mock"}]
    import proposer as PR
    text, u = PR.safe_chat(messages, max_tokens=max_tokens); uses = [u]
    if not (text or "").strip() and u.get("finish") == "length":
        text, u2 = BP._chat_effort(messages, max_tokens, "medium"); uses.append({**u2, "effort": "medium"})
    return BP._strip_think(text), uses


REPAIR = """Below is a draft written by an engineer who analysed when a harness rule helps and when it harms. Rewrite it into EXACTLY {k}
candidates in this format, keeping the engineer's logic (do not invent new logic; complete any code that was cut off):

NAME: <snake_case>
KIND: <same kind as the parent rule>
CLASS: <control_flow or task_knowledge>
HYPOTHESIS: <one or two sentences>
```python
NOTE = None
def detect(view):
    ...
```
Rules: detect(view) is the CHILD condition only (it is ANDed with the parent rule automatically); use only view["task"], view["step"],
view["cells"] (list of dicts with code/out/error), view["pending"]; imports only inside detect (re, json, math, collections, string).

DRAFT:
{draft}"""


def repair_format(draft, k, max_tokens):
    if os.environ.get("BOOST_MOCK") == "1": return _mock_chat([{"role": "user", "content": draft}]), [{"in": 0, "out": 0, "finish": "mock"}]
    import proposer as PR, bit_propose as BP
    msgs = [{"role": "user", "content": REPAIR.format(k=k, draft=BP._strip_think(draft or "")[-14000:])}]
    text, u = PR.safe_chat(msgs, max_tokens=min(max_tokens, 6000), thinking=False)
    return BP._strip_think(text), [{**u, "repair": True}]


def self_check(sp, states, eps_by, max_steps, timeout):
    """-> (patch_src | None, self_check dict, why); why == "" iff the child passes."""
    try: src, fk = fires_at_k(sp, states, eps_by, max_steps, timeout)
    except (ValueError, R.SimulationError) as e: return None, {}, f"the compiled child failed: {str(e)[:300]}"
    helped = [s for s in states if s["group"] == "helped"]; harmed = [s for s in states if s["group"] == "harmed"]
    neg = harmed or [s for s in states if s["d"] <= 0]; tgt = "harmed" if harmed else "harmed or neutral"
    kh = [s["sid"] for s in helped if fk[s["sid"]]["kept"]]; kn = [s["sid"] for s in neg if fk[s["sid"]]["kept"]]
    sc = {"kept": [s["sid"] for s in states if fk[s["sid"]]["kept"]], "kept_helped": kh, "kept_neg": kn, "n_helped": len(helped), "n_neg": len(neg),
          "neg_group": tgt, "moved": [s["sid"] for s in states if fk[s["sid"]]["k_fire"] not in (None, s["k"])],
          "hook_errors": sum(v["hook_errors"] or 0 for v in fk.values())}
    err = f" detect raised an exception {sc['hook_errors']} time(s) (an exception counts as no fire)." if sc["hook_errors"] else ""
    if helped and not kh:
        return src, sc, f"parent AND child fired at the firing step on none of the {len(helped)} helped states ({', '.join(s['sid'] for s in helped)}); it must keep at least one.{err}"
    if neg and len(kn) == len(neg):
        return src, sc, f"parent AND child still fires at the firing step on every {tgt} state ({', '.join(kn)}); it must drop at least one of them.{err}"
    return src, sc, ""


FIX = ("Child {name}: {why}\nRewrite this one child to fix the problem. Reply with exactly one child in the same format (NAME:, HYPOTHESIS:, then one "
       "```python block with NOTE = None or a refined note, and def detect(view):).")
NONE_FOUND = "Your reply contained no child in the required format. Write the {k} children now: NAME:, HYPOTHESIS:, then one ```python block each."


def cmd_propose(a):
    node = json.load(open(a.node, encoding="utf-8"))
    parent = json.load(open(a.parent_spec, encoding="utf-8")) if a.parent_spec else node.get("parent_spec")
    if not parent: sys.exit("no parent spec: pass --parent-spec")
    parent = parent.get("spec", parent); parent.setdefault("origin", {}); parent["origin"] = {**(parent["origin"] or {}), "cid": node["cid"]}
    runs = a.runs or node["runs"]; instr = a.instr or node["instr"]; results = a.results or node["results"]
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", a.run_id): sys.exit("--run-id must be [A-Za-z0-9_-]+")
    eps_by = _load_eps(runs, instr); states = [s for s in node["states"] if s["eid"] in eps_by]
    if len(states) < len(node["states"]): print(f"  ! {len(node['states']) - len(states)} node state(s) have no episode in --runs; left out")
    bench = a.bench if a.bench != "auto" else ("gaia2" if any(e.get("bench") == "gaia2" for e in eps_by.values()) else "appworld")
    max_steps = a.max_steps or _max_steps(list(eps_by.values()))
    node = {**node, "states": states}
    msgs = [{"role": "system", "content": "You review logs of an LLM agent (a model like yourself) and refine harness rules: you find where a rule "
                                          "helps and where it hurts, and write small, general detector programs that separate the two."},
            {"role": "user", "content": build_prompt(node, parent, eps_by, results, a.k, max_steps, bench, a.max_show)}]
    if a.dry_run:
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
        print(f"### SYSTEM\n{msgs[0]['content']}\n\n### USER\n{msgs[1]['content']}"); return
    t0 = time.time(); text, uses = ask(msgs, a.max_tokens); kids = [c for c in R.parse_proposals(text) if c.get("detect_src")]; nw = 0
    raw_first = text
    while not kids and nw < MAX_RETRIES:
        # format repair in a FRESH, short context with thinking off: the analysis is done, only the output format failed
        # (a long thinking reply hit the length limit, or code was written without fences). No conversation accumulation.
        nw += 1; text, u = repair_format(raw_first, a.k, a.max_tokens); uses += u
        kids = [c for c in R.parse_proposals(text) if c.get("detect_src")]
    diagnosis = (text.split("NAME:", 1)[0] if kids else text).strip()[:2000]
    base = {"run": a.run_id, "case_id": node["cid"], "parent_cid": node["cid"], "task": None, "node": a.node, "diagnosis": diagnosis}
    if os.path.dirname(a.out): os.makedirs(os.path.dirname(a.out), exist_ok=True)
    lines = []
    if not kids:
        lines.append({"cid": f"{a.run_id}_1", **base, "spec": None, "valid": False, "why": "no child in the reply", "self_check": {},
                      "patch_path": None, "attempts": nw + 1, "usage": {"calls": uses}, "raw": text, "raw_first": raw_first})
    for j, kid in enumerate(kids[:a.k], 1):
        cid = f"{a.run_id}_{j}"; cu = list(uses) if j == 1 else []; raw = text; hist = []; cconv = conv; sp = None; src = None; sc = {}
        for att in range(MAX_RETRIES + 1):
            try: sp = child_spec(parent, kid, cid); src, sc, why = self_check(sp, states, eps_by, max_steps, a.sim_timeout)
            except ValueError as e: sp, src, sc, why = None, None, {}, f"rejected by the validator: {e}"
            hist.append({"name": kid.get("name"), "why": why})
            if not why or att == MAX_RETRIES: break
            cconv = cconv + [{"role": "user", "content": FIX.format(name=kid.get("name") or f"#{j}", why=why)}]
            rt, u = ask(cconv, a.max_tokens); cu += u; cconv = cconv + [{"role": "assistant", "content": rt}]; raw = rt
            new = R.parse_proposals(rt); kid = new[0] if new else {**kid, "detect_src": ""}
        path = None
        if src:
            os.makedirs(a.patch_dir, exist_ok=True); fp = os.path.join(a.patch_dir, f"{cid}.py")
            with open(fp, "w", encoding="utf-8") as f: f.write(src)
            ap_ = os.path.abspath(fp); path = os.path.relpath(ap_, AW).replace("\\", "/") if ap_.startswith(os.path.abspath(AW) + os.sep) else ap_
        lines.append({"cid": cid, **base, "spec": sp, "child": {"name": kid.get("name"), "hypothesis": kid.get("hypothesis"), "note": kid.get("note"),
                      "detect_src": kid.get("detect_src")}, "valid": not why, "why": why, "self_check": sc, "patch_path": path,
                      "attempts": len(hist), "history": hist, "usage": {"in": sum(x.get("in") or 0 for x in cu), "out": sum(x.get("out") or 0 for x in cu),
                                                                       "calls": cu}, "raw": raw, "secs": round(time.time() - t0, 1)})
    with open(a.out, "w", encoding="utf-8") as fh:
        for l in lines: fh.write(json.dumps(l, ensure_ascii=False) + "\n")
    for l in lines:
        sc = l["self_check"] or {}
        print(f"  {l['cid']:10s} {str((l['child'] or {}).get('name') if l.get('child') else None)[:36]:36s} valid={l['valid']!s:5s} "
              f"kept helped {len(sc.get('kept_helped', []))}/{sc.get('n_helped', '-')} {sc.get('neg_group', 'neg')} {len(sc.get('kept_neg', []))}/{sc.get('n_neg', '-')}"
              f"{'' if l['valid'] else '  why: ' + l['why'][:120]}")
    print(f"{a.run_id}: {len(lines)} children, {sum(l['valid'] for l in lines)} valid -> {a.out} ({time.time() - t0:.0f}s)")


# ---------------------------------------------------------------- evaluate
def cmd_evaluate(a):
    import bit_branch as BB, bit_lowrank as LR, bit_tree as BT
    node = json.load(open(a.node, encoding="utf-8")); runs = a.runs or node["runs"]; instr = a.instr or node["instr"]
    eps_all = load_episodes(runs, instr); eps_by = {e["eid"]: e for e in eps_all if not e["crashed"]}
    states = [s for s in node["states"] if s["eid"] in eps_by]; max_steps = a.max_steps or _max_steps(list(eps_by.values()))
    if len(states) < len(node["states"]): print(f"  ! {len(node['states']) - len(states)} node state(s) have no episode in --runs; left out")
    LR.node_prior.tries = BT.build_tries([e for e in eps_all if not e["crashed"] and not e["has_replay"]]); prior_eps = list(eps_by.values())
    d = np.array([s["d"] for s in states], float)
    cands = []
    for p in [x for x in (a.cands or "").split(",") if x]:
        for line in open(p, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if r.get("valid") and r.get("spec"): cands.append((r["cid"], r["spec"]))
    for p in [x for x in (a.specs or "").split(",") if x]:
        sp = json.load(open(p, encoding="utf-8")); sp = sp.get("spec", sp); cands.append(((sp.get("origin") or {}).get("cid") or sp["name"], sp))

    def pooled(sel):
        sts = []
        try:
            for s in sel:
                v0 = min(max(LR.node_prior(prior_eps, s["eid"], s["k"]), 0.02), 0.98)
                sts.append({**s, "v0": v0, "nw": s["nw"] + int(s["logged_won"]), "nn": s["nn"] + 1})   # logged run = a free none sample (bit_lowrank --use-logged 1)
        except (KeyError, StopIteration): return None   # episode not in the trie (replayed / crashed base episode)
        return LR.posterior(sts) if sts else None

    rows = []
    for cid, sp in cands:
        try: _, fk = fires_at_k(sp, states, eps_by, max_steps, a.timeout)
        except (ValueError, R.SimulationError) as e: print(f"  ! {cid}: {str(e)[:200]}"); continue
        kept = np.array([bool(fk[s["sid"]]["kept"]) for s in states]); L = [s for s, m in zip(states, kept) if m]; Rr = [s for s, m in zip(states, kept) if not m]
        g = split_gain(d, kept, a.lam, a.gamma); pk = BB.post_p_pos(L); pr = pooled(L)
        rows.append({"cid": cid, "name": sp.get("name"), "gain": g, "n_kept": len(L), "n_dropped": len(Rr), "kept": [s["sid"] for s in L],
                     "dropped": [s["sid"] for s in Rr], "moved": [s["sid"] for s in states if fk[s["sid"]]["k_fire"] not in (None, s["k"])],
                     "sum_d_kept": float(sum(s["d"] for s in L)), "sum_d_dropped": float(sum(s["d"] for s in Rr)),
                     "a_kept": float(np.mean([s["d"] for s in L])) if L else None, "a_dropped": float(np.mean([s["d"] for s in Rr])) if Rr else None,
                     "p_pos_kept": pk, "p_pos_dropped": BB.post_p_pos(Rr), "pooled_kept": pr, "value_removed": float(-sum(s["d"] for s in Rr)),
                     "dropped_harmed": sum(s["d"] < 0 for s in Rr), "dropped_helped": sum(s["d"] > 0 for s in Rr),
                     "leaf_kept": "intervene" if (pk or 0) >= a.p_leaf else "none", "hook_errors": sum(v["hook_errors"] or 0 for v in fk.values()),
                     "spec": sp})
    rows.sort(key=lambda r: -r["gain"])
    best = next((r for r in rows if r["gain"] > 0 and r["n_kept"] > 0), None)   # gamma is already subtracted
    n = len(states); warn = [] if n >= a.min_child_weight else [f"node has {n} < {a.min_child_weight} states (min_child_weight): do not split"]
    f = lambda v, fmt="+.3f": "  -  " if v is None else format(v, fmt)
    print(f"node {node['cid']}: {n} states, sum d = {d.sum():+.2f}, lam = {a.lam}, gamma = {a.gamma}{'; ' + warn[0] if warn else ''}")
    print(f"{'cid':12s} {'name':32s}  gain  kept/drop moved  a_kept  P(a_k>0) pooled a_k [90%]        value_rm drop(harm/help) leaf")
    for r in rows:
        pk = r["pooled_kept"] or {}
        print(f"{r['cid'][:12]:12s} {str(r['name'])[:32]:32s} {r['gain']:+.3f} {r['n_kept']:3d}/{r['n_dropped']:<3d} {len(r['moved']):4d}  {f(r['a_kept'])}  "
              f"{f(r['p_pos_kept'], '.3f'):6s}   {f(pk.get('a_bar'))} [{f(pk.get('a_lo90'))},{f(pk.get('a_hi90'))}] {r['value_removed']:+6.2f}   "
              f"{r['dropped_harmed']}/{r['dropped_helped']}      {r['leaf_kept']}")
    rec = best["cid"] if best and not warn else None
    print(f"recommended: {rec or 'none (no child with Gain > gamma)' if not warn else 'none'}"
          + (f"  (next: out-of-node check with `heldout`; admit if P(a_kept>0) >= 0.9 on >= 4 held-out states)" if rec else ""))
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.node)), "eval_" + os.path.splitext(os.path.basename(a.node))[0] + ".json")
    json.dump({"node": a.node, "params": {"lam": a.lam, "gamma": a.gamma, "p_leaf": a.p_leaf, "min_child_weight": a.min_child_weight},
               "parent": {**node["stats"], "n_eval": n}, "warnings": warn, "children": rows, "recommended": rec},
              open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if rec and a.spec_out:
        json.dump(best["spec"], open(a.spec_out, "w", encoding="utf-8"), indent=1, ensure_ascii=False); print(f"spec of {rec} -> {a.spec_out}")
    print(f"-> {out}")


# ---------------------------------------------------------------- heldout
def _filter_run(src, dst, drop):
    """copy of a run JSON without the episodes whose eid is in drop (every per-episode list of length n_games is filtered)."""
    d = json.load(open(src, encoding="utf-8")); n = len(d["games"]); pre = f"{d['tag']}_s{d['seed']}:"
    keep = [i for i, t in enumerate(d["games"]) if pre + t not in drop]
    for k, v in list(d.items()):
        if isinstance(v, list) and len(v) == n: d[k] = [v[i] for i in keep]
    d["n_games"] = len(keep); json.dump(d, open(dst, "w", encoding="utf-8")); return n - len(keep)


def cmd_heldout(a):
    import bit_branch as BB
    sp = json.load(open(a.child_spec, encoding="utf-8")); cid = a.cid or sp.get("cid") or ((sp.get("spec") or sp).get("origin") or {}).get("cid")
    sp = sp.get("spec", sp); cid = re.sub(r"[^A-Za-z0-9_.-]", "_", cid or sp["name"]); R.validate_spec(sp)
    excl, node_tasks = set(), set()
    for x in [x for x in a.exclude_eids.split(",") if x]:
        if x.endswith(".json") and os.path.exists(x):
            nd = json.load(open(x, encoding="utf-8")); excl |= {s["eid"] for s in nd["states"]}; node_tasks |= {s["task"] for s in nd["states"]}
        else: excl.add(x); node_tasks.add(x.split(":", 1)[-1])
    runs = [p for p in a.runs.split(",") if p]; eps = load_episodes(runs, a.instr)
    if a.exclude_node_tasks: excl |= {e["eid"] for e in eps if e["task"] in node_tasks}
    tmp = tempfile.mkdtemp(prefix="bit_heldout_"); fr = []
    try:
        for j, p in enumerate(runs):
            q = os.path.join(tmp, f"{j:02d}_{os.path.basename(p)}"); n = _filter_run(p, q, excl); fr.append(q)
            print(f"  {os.path.basename(p)}: {n} episode(s) excluded")
        os.makedirs(a.out, exist_ok=True); scr = os.path.join(a.out, "heldout_screen.json")
        json.dump({"params": {"heldout_of": a.exclude_eids}, "candidates": [{"cid": cid, "spec": sp}], "kept": []}, open(scr, "w", encoding="utf-8"), indent=1)
        ns = argparse.Namespace(screen=scr, cands="", refs="", runs=",".join(fr), instr=a.instr, out=a.out, round=a.round, reps=a.reps,
                                max_states=a.max_states, env_file=a.env_file, force_cid=[cid], server_root=a.server_root, server_out=a.server_out,
                                qsub=a.qsub, workers=a.workers, timeout=a.timeout, base_specs=a.base_specs, harness_cmd=a.harness_cmd)
        BB.build(ns)
    finally: shutil.rmtree(tmp, ignore_errors=True)
    mp = os.path.join(a.out, "manifest.json"); man = json.load(open(mp, encoding="utf-8"))
    man["runs"] = a.runs; man["heldout"] = {"excluded_eids": sorted(excl), "exclude_node_tasks": a.exclude_node_tasks, "child_spec": a.child_spec}
    json.dump(man, open(mp, "w"), indent=1)
    got = []
    for c in man["cands"]:
        for dd in c["dirs"]:
            got += [m["eid"] for m in json.load(open(os.path.join(a.out, dd["dir"], "meta.json"), encoding="utf-8")).values()]
    leak = sorted(set(got) & excl)
    if leak: sys.exit(f"held-out build contains excluded episodes: {leak}")
    print(f"held-out: {len(got)} state(s) outside the node ({len(excl)} episode(s) excluded) -> {os.path.join(a.out, 'jobs.txt')}")
    if len(got) < 4: print(f"  ! fewer than 4 held-out states: admission needs >= 4 (add active-sampling seeds on the parent's firing tasks)")


# ---------------------------------------------------------------- mock (BOOST_MOCK=1; offline tests only)
_M_NOTQ = '''NAME: task_not_question
HYPOTHESIS: mock: the parent hurts on tasks that ask a question (they need the answer); keep it only where the task asks no question.
```python
NOTE = None
def detect(view):
    return "?" not in (view["task"] or "")
```
'''
_M_ALWAYS = '''NAME: always_true_child
HYPOTHESIS: mock: does not split (keeps every state); must fail the self-check.
```python
NOTE = None
def detect(view):
    return True
```
'''
_M_GETATTR = '''NAME: uses_getattr_child
HYPOTHESIS: mock: invalid on purpose (forbidden name).
```python
NOTE = None
def detect(view):
    return getattr(view, "task", None)
```
'''
_M_FIXED = '''NAME: no_question_mark_refined
HYPOTHESIS: mock: fixed child (no forbidden name) with a refined note.
```python
NOTE = "This task asks you to DO something and does not ask a question. If it is done, call apis.supervisor.complete_task() with no answer."
def detect(view):
    import re
    return not re.search(r"\\?", view["task"] or "")
```
'''


def _mock_chat(messages):
    turn = sum(1 for m in messages if m["role"] == "assistant"); last = messages[-1]["content"]
    if turn == 0: return "Mock diagnosis: the harmed states are question tasks.\n\n" + _M_NOTQ + "\n" + _M_ALWAYS + "\n" + _M_GETATTR
    if "always_true_child" in last: return _M_ALWAYS   # stays broken -> invalid after the retries
    return _M_FIXED


# ---------------------------------------------------------------- CLI
def main():
    import bit_branch as BB
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("nodes"); n.add_argument("--builds", required=True); n.add_argument("--results", default="results")
    n.add_argument("--runs", required=True); n.add_argument("--instr", required=True); n.add_argument("--cid", required=True)
    n.add_argument("--out", required=True); n.add_argument("--parent-spec", default="", help="override the spec stored in the manifests")
    n.add_argument("--lam", type=float, default=1.0)
    p = sub.add_parser("propose"); p.add_argument("--node", required=True); p.add_argument("--parent-spec", default="")
    p.add_argument("--runs", default=""); p.add_argument("--instr", default=""); p.add_argument("--results", default="")
    p.add_argument("--out", required=True); p.add_argument("--run-id", required=True); p.add_argument("--k", type=int, default=3)
    p.add_argument("--max-tokens", type=int, default=16000); p.add_argument("--sim-timeout", type=float, default=60)
    p.add_argument("--max-steps", type=int, default=None); p.add_argument("--max-show", type=int, default=8, help="states shown per group")
    p.add_argument("--bench", choices=["auto", "appworld", "gaia2"], default="auto"); p.add_argument("--patch-dir", default=os.path.join(AW, "patches_ccbit"))
    p.add_argument("--dry-run", action="store_true", help="print the prompt and exit (no calls)")
    e = sub.add_parser("evaluate"); e.add_argument("--node", required=True); e.add_argument("--cands", default="")
    e.add_argument("--specs", default="", help="extra full child specs (JSON files) to evaluate"); e.add_argument("--runs", default="")
    e.add_argument("--instr", default=""); e.add_argument("--lam", type=float, default=1.0); e.add_argument("--gamma", type=float, default=0.0)
    e.add_argument("--p-leaf", type=float, default=0.9); e.add_argument("--min-child-weight", type=int, default=4)
    e.add_argument("--max-steps", type=int, default=None); e.add_argument("--timeout", type=float, default=120)
    e.add_argument("--out", default=""); e.add_argument("--spec-out", default="", help="write the recommended child's spec here")
    h = sub.add_parser("heldout"); h.add_argument("--child-spec", required=True); h.add_argument("--cid", default="")
    h.add_argument("--runs", required=True); h.add_argument("--instr", required=True)
    h.add_argument("--exclude-eids", required=True, help="comma list of node.json files and/or episode ids")
    h.add_argument("--exclude-node-tasks", action="store_true", help="also leave out every episode of the node's tasks")
    h.add_argument("--out", required=True); h.add_argument("--round", required=True); h.add_argument("--env-file", required=True)
    h.add_argument("--reps", type=int, default=2); h.add_argument("--max-states", type=int, default=40); h.add_argument("--timeout", type=float, default=300)
    h.add_argument("--server-root", default=BB.SERVER_ROOT); h.add_argument("--server-out", default=""); h.add_argument("--qsub", default="")
    h.add_argument("--workers", type=int, default=8); h.add_argument("--base-specs", default="", help="trees already in the base harness")
    h.add_argument("--harness-cmd", default=BB.HARNESS_CMD, help=f"harness command of the job lines (Gaia2: {BB.GAIA2_CMD!r})")
    a = ap.parse_args()
    {"nodes": cmd_nodes, "propose": cmd_propose, "evaluate": cmd_evaluate, "heldout": cmd_heldout}[a.cmd](a)


if __name__ == "__main__":
    main()
