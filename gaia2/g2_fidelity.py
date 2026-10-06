"""Live-vs-simulate fidelity of a compiled BIT patch on Gaia2 (GAIA2_ADAPTER_PLAN §5 server step 7): the steps at which a patched
live run (bos_gaia2.py eval --patch P) recorded fires ("fired") must equal appworld/boost/bit_rubric.simulate(P) on that same log.
A blocked / rewritten cell is logged as the replacement; the cell the model wrote is put back first (traj "code_pre", logged in
full by bos_gaia2; else the patch's fired["pending"], which is cut at 300 chars). Exit 1 on any mismatch.
usage: python gaia2/g2_fidelity.py --result gaia2/results/T_seedS.json --patch P.py [--instr gaia2/data/instructions_all.json]"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "appworld", "boost"))


def main():
    import bit_common, bit_rubric
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--result", required=True); ap.add_argument("--patch", required=True)
    ap.add_argument("--instr", default=os.path.join(HERE, "data", "instructions_all.json")); a = ap.parse_args()
    R = json.load(open(a.result, encoding="utf-8")); src = open(a.patch, encoding="utf-8").read()
    eps = bit_common.load_episodes([a.result], json.load(open(a.instr, encoding="utf-8"))); trunc = set()
    for i, e in enumerate(eps):
        for f in R["fired"][i]:
            tr = R["traj"][i][f["step"]]
            orig = tr.get("code_pre") or (f.get("pending") if f.get("kind") == "block_once" else None)
            if not orig: continue
            if not tr.get("code_pre") and len(orig) >= 300: trunc.add(e["eid"])
            for s in e["steps"]:
                if s["k"] == f["step"]: s["code"] = orig
    sim = bit_rubric.simulate(src, eps, stop_at_first=False, timeout_s=120); ok = True
    for i, e in enumerate(eps):
        live = [(f.get("step"), f.get("eid")) for f in R["fired"][i]]
        pred = [(f["k"], f["eid"]) for f in sim[e["eid"]]["fires"]]
        ok = ok and live == pred
        print(f"{'OK ' if live == pred else 'BAD'} {e['task']} steps={len(e['steps'])} live={live} sim={pred} hook_errors={sim[e['eid']]['hook_errors']}"
              + (" (pending cut at 300 chars)" if e["eid"] in trunc else ""))
    print(f"fidelity {'PASS' if ok else 'FAIL'}: {len(eps)} episodes, {sum(bool(f) for f in R['fired'])} with fires")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
