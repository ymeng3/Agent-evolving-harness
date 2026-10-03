"""Branch-at-fire evaluation, build step (MATH_FORMALIZATION sections 2 and 4: local estimate of a_k at the detector's firing state).

For each logged H1 episode, re-run the E_GROUNDED detector logic over its cells to find the firing states. Then write, per (slot, origin seed):
  tasks.json      task ids that have a firing state in that slot
  replay.json     tid -> logged codes before the firing step (BOS_REPLAY; replayed exactly, no LLM call)
  hints_<v>.json  tid -> note text for variant v (BOS_HINTS; injected once by patches_ccdiag/BRANCH_NOTE.py at the first live step)
Slots: 'first' = the first non-D7 firing (D2 / D6 / D8'); 'endgame' = the D7 firing (<= 3 steps left, no complete_task).
Variants: none (plain continuation = resampling from the same state), plain (RUBRIC_NUDGES_H1 wording), grounded (RUBRIC_GROUNDED_H1 wording).
The replay must use the episode's original AppWorld seed, so each (slot, origin seed) is one run per variant.
usage: python boost/branch_build.py --runs A.json,B.json --out branch/NAME"""
import argparse, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PLAIN = {   # RUBRIC_NUDGES_H1 wording, keyed by detector (D8' has no counterpart there: H1 debounces exact repeats)
    "D2": "Your last two cells did the same thing for different items. Put ALL remaining items in ONE loop in a single cell (collect the results in a list and print a compact summary).",
    "D6": "apis.amazon.place_order needs an address_id and a payment_card_id from apis.amazon.show_addresses and apis.amazon.show_payment_cards (the supervisor lists have no IDs). Fetch both in one cell.",
    "D7": "Only {left} step(s) left. Do the remaining state-changing call(s) now and call apis.supervisor.complete_task() (with answer=... if the task asks a question) in this step if at all possible. Do not spend steps on docs or verification.",
}


def grounded_fn():
    ns = {}; exec(open(os.path.join(HERE, "..", "patches_ccdiag", "RUBRIC_GROUNDED_H1.py"), encoding="utf-8").read(), ns)
    return ns["e1_pre_call"], ns["e1_post_exec"]


def firings(traj, max_steps=30):
    """-> list of (step k, detector, grounded note, left). k = index of the step whose prompt carries the note (cells 0..k-1 executed)."""
    pre_call, post_exec = grounded_fn(); st = {}; out = []
    for k in range(min(len(traj), max_steps)):
        before = dict(st.get("last_fired", {}))
        p = pre_call("", st)
        if p:
            det = [d for d, s in st["last_fired"].items() if before.get(d) != s][0]
            out.append((k, det, p.split("[harness note] ", 1)[1], max_steps - k))
        post_exec(traj[k].get("code") or "", traj[k].get("out") or "", st)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--runs", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    groups = {}   # (slot, seed) -> {tid: (codes, det, grounded, left)}
    for p in a.runs.split(","):
        d = json.load(open(p, encoding="utf-8")); seed = d["seed"]
        assert d.get("harness_h1"), f"{p}: branch evaluation needs H1 logs (exact replay without evaluate)"
        for tid, tr, cr in zip(d["games"], d["traj"], d.get("crashed") or [None] * len(d["games"])):
            if cr or any(s.get("replayed") for s in tr): continue
            fs = firings(tr)
            first = next((f for f in fs if f[1] != "D7"), None); end = next((f for f in fs if f[1] == "D7"), None)
            for slot, f in (("first", first), ("endgame", end)):
                if f: groups.setdefault((slot, seed), {}).setdefault(tid, ([s.get("code") or "" for s in tr[:f[0]]], *f[1:]))
    os.makedirs(a.out, exist_ok=True); manifest = []
    for (slot, seed), m in sorted(groups.items()):
        dd = os.path.join(a.out, f"{slot}_s{seed}"); os.makedirs(dd, exist_ok=True)
        json.dump(sorted(m), open(f"{dd}/tasks.json", "w"))
        json.dump({t: v[0] for t, v in m.items()}, open(f"{dd}/replay.json", "w"))
        json.dump({t: v[2] for t, v in m.items()}, open(f"{dd}/hints_grounded.json", "w"), indent=1)
        json.dump({t: PLAIN[v[1]].format(left=v[3]) for t, v in m.items() if v[1] in PLAIN}, open(f"{dd}/hints_plain.json", "w"), indent=1)
        json.dump({t: {"det": v[1], "k": len(v[0])} for t, v in m.items()}, open(f"{dd}/meta.json", "w"))
        dets = {}
        for v in m.values(): dets[v[1]] = dets.get(v[1], 0) + 1
        manifest.append({"dir": dd, "slot": slot, "seed": seed, "n": len(m), "dets": dets})
        print(f"{slot:8s} seed {seed}: {len(m)} states {dets}")
    json.dump(manifest, open(os.path.join(a.out, "manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
