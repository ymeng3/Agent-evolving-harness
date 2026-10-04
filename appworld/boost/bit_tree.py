"""BIT Unit B: memory tree + residual report (docs/design/BOOSTED_INTERVENTION_TREES_v0.md sections 2-3, BIT_IMPLEMENTATION_PLAN Unit B).
One prefix trie per task over the logged steps of all (non-crashed) episodes; a node = a prefix state, keyed per step on
(whitespace-normalized executed code, out[:200]). Each node carries the win/loss counts of the episodes passing through it, the Beta
posterior of p, the XGBoost-style residual g = p-1, h = p(1-p), and priority g^2/(h+lam) + kappa*sd (Newton gain + exploration).
Cases = one per lost episode, paired with the same-task won episode sharing the longest prefix (the "won sibling"); the proposer reads these.
usage: python boost/bit_tree.py --runs A.json,B.json --instr instructions_all100.json --out bit/<R>/tree.json
                                [--top 20] [--max-per-task 2] [--exclude tid1,tid2] [--branch-meta ...]"""
import argparse, collections, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bit_common import load_episodes, beta_stats


def step_key(s):
    return (" ".join((s.get("code") or "").split()), (s.get("out") or "")[:200])


def _node_id(tid, path):
    return f"{tid}/{len(path)}/" + hashlib.sha1(json.dumps(path, ensure_ascii=False).encode("utf-8")).hexdigest()[:8]


def build_tries(eps):
    """-> {tid: root}; node = {"id","depth","won":[eid],"lost":[eid],"children":{key: node}}. Episodes counted at every node on their path
    (root included); crashed episodes must already be filtered out."""
    tries = {}
    for e in eps:
        node = tries.setdefault(e["task"], {"id": _node_id(e["task"], []), "depth": 0, "won": [], "lost": [], "children": {}})
        path = []
        node["won" if e["won"] else "lost"].append(e["eid"])
        for s in e["steps"]:
            k = step_key(s); path.append(list(k))
            if k not in node["children"]:
                node["children"][k] = {"id": _node_id(e["task"], path), "depth": len(path), "won": [], "lost": [], "children": {}}
            node = node["children"][k]
            node["won" if e["won"] else "lost"].append(e["eid"])
    return tries


def node_at(tries, ep, depth):
    """Trie node on episode ep's path at the given depth (0 = root; clipped to the episode length). Used by screening (Unit E)."""
    node = tries[ep["task"]]
    for s in ep["steps"][:depth]: node = node["children"][step_key(s)]
    return node


def common_prefix(a, b):
    n = 0
    for x, y in zip(a["steps"], b["steps"]):
        if step_key(x) != step_key(y): break
        n += 1
    return n


def _walk(node):
    yield node
    for c in node["children"].values(): yield from _walk(c)


def build_tree(eps, runs, top=20, max_per_task=2):
    eps = [e for e in eps if not e["crashed"]]
    tries = build_tries(eps); by_task = collections.defaultdict(list)
    for e in eps: by_task[e["task"]].append(e)
    out = {"runs": list(runs),
           "episodes": {e["eid"]: {"task": e["task"], "tag": e["tag"], "seed": e["seed"], "won": e["won"], "G": e["G"], "n_steps": len(e["steps"])}
                        for e in eps},
           "tasks": {}, "nodes": [], "cases": []}
    for t in sorted(by_task):
        es = by_task[t]; w = sum(e["won"] for e in es)
        out["tasks"][t] = {"n": len(es), "wins": w, "mixed": 0 < w < len(es), **beta_stats(w, len(es) - w), "eids": [e["eid"] for e in es]}
    for t in sorted(tries):
        for v in _walk(tries[t]):
            if v["depth"] == 0 or len(v["children"]) > 1:
                out["nodes"].append({"node": v["id"], "task": t, "depth": v["depth"], "n_win": len(v["won"]), "n_loss": len(v["lost"]),
                                     **beta_stats(len(v["won"]), len(v["lost"])), "eids_won": list(v["won"]), "eids_lost": list(v["lost"])})
    out["nodes"].sort(key=lambda n: (-n["priority"], n["task"], n["depth"], n["node"]))
    cases = []
    for t in sorted(by_task):
        won = [e for e in by_task[t] if e["won"]]
        for e in [e for e in by_task[t] if not e["won"]]:
            if won:
                fd, sib = max(((common_prefix(e, s), s) for s in won), key=lambda x: (x[0], -won.index(x[1])))
                v = node_at(tries, e, fd); pr = beta_stats(len(v["won"]), len(v["lost"]))["priority"]
                cases.append({"task": t, "lost": e["eid"], "won": sib["eid"], "fork_depth": fd, "priority": pr})
            else:
                r = tries[t]; pr = 0.5 * beta_stats(len(r["won"]), len(r["lost"]))["priority"]
                cases.append({"task": t, "lost": e["eid"], "won": None, "fork_depth": 0, "priority": pr})
    cases.sort(key=lambda c: (-c["priority"], c["task"], c["lost"]))
    per = collections.Counter(); kept = []
    for c in cases:
        if len(kept) >= top: break
        if per[c["task"]] >= max_per_task: continue
        per[c["task"]] += 1; kept.append(c)
    out["cases"] = [{"case_id": f"c{i + 1:02d}", **c} for i, c in enumerate(kept)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="comma list of run logs (results/*.json)")
    ap.add_argument("--instr", required=True, help="json tid -> instruction")
    ap.add_argument("--out", required=True, help="bit/<R>/tree.json")
    ap.add_argument("--top", type=int, default=20); ap.add_argument("--max-per-task", type=int, default=2)
    ap.add_argument("--exclude", default="", help="comma list of task ids to leave out entirely")
    # TODO(BIT round 2): attach branch-at-fire continuations (bit_branch build meta.json) as sibling subtrees at their fire node.
    # Accepted and ignored for now.
    ap.add_argument("--branch-meta", default="", help="(TODO, ignored) branch build meta to graft branch continuations onto the trie")
    a = ap.parse_args()
    runs = [p for p in a.runs.split(",") if p]; excl = {x for x in a.exclude.split(",") if x}
    instr = json.load(open(a.instr, encoding="utf-8"))
    eps = [e for e in load_episodes(runs, instr) if e["task"] not in excl]
    if a.branch_meta: print("note: --branch-meta is not implemented yet; ignored")
    tree = build_tree(eps, runs, a.top, a.max_per_task)
    if os.path.dirname(a.out): os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(tree, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    ne = len(tree["episodes"]); nw = sum(e["won"] for e in tree["episodes"].values())
    print(f"{ne} episodes ({nw} won, {ne - nw} lost), {len(tree['tasks'])} tasks ({sum(t['mixed'] for t in tree['tasks'].values())} mixed), "
          f"{len(tree['nodes'])} root/fork nodes, {len(tree['cases'])} cases -> {a.out}")
    for c in tree["cases"]:
        print(f"  {c['case_id']} {c['task']:12s} prio={c['priority']:.5f} fork@{c['fork_depth']:<3d} lost={c['lost']}  won={c['won']}")


if __name__ == "__main__":
    main()
