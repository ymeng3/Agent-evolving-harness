"""Failed-test descriptions for the lost episodes of a BIT tree (privileged hindsight for the self-proposer, prereg A24).
Replays each logged episode exactly in AppWorld (H1 setup + logged cells, no LLM calls), then reads world.evaluate().failures.
Output JSON {eid: ["<requirement>", ...]} (default: requirement text only) or with --with-trace "<requirement> | <assertion message>"
(the assertion message can contain ground-truth values: stronger privilege, reported as a separate ablation). Discovery split only.
usage (server, appworld/): python boost/bit_failed_tests.py --tree bit/R0/tree.json --runs A.json,B.json --out bit/R0/failed_tests.json"""
import argparse, json, os, sys


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tree", required=True); ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--with-trace", action="store_true"); a = ap.parse_args()
    sys.argv = sys.argv[:1]; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import bos_appworld_v3 as V
    from appworld import AppWorld
    tree = json.load(open(a.tree)); want = {c["lost"] for c in tree["cases"]}; out = {}
    for p in a.runs.split(","):
        d = json.load(open(p)); tag, seed = d["tag"], d["seed"]
        for t, tr in zip(d["games"], d["traj"]):
            eid = f"{tag}_s{seed}:{t}"
            if eid not in want: continue
            with AppWorld(task_id=t, experiment_name=f"cc_bit_failtests_{tag}_s{seed}", random_seed=seed) as w:
                if d.get("harness_h1"): w.execute(V.H1_SETUP)
                for s in tr:
                    if s.get("code"): w.execute(s["code"])
                    if w.task_completed(): break
                ev = w.evaluate().to_dict()
            fl = []
            for f in ev.get("failures", []):
                req = " ".join(str(f.get("requirement", "")).split())
                if a.with_trace:
                    msg = str(f.get("trace", "")).split("----------")[-1].strip().splitlines()
                    req += " | " + (msg[-1][:200] if msg else "")
                fl.append(req)
            out[eid] = fl; print(eid, fl, flush=True)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); json.dump(out, open(a.out, "w"), indent=1)
    print(f"{len(out)} episodes -> {a.out}")


if __name__ == "__main__":
    main()
