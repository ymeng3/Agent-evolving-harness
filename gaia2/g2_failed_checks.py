"""Gaia2 counterpart of appworld/boost/bit_failed_tests.py (docs/design/GAIA2_ADAPTER_PLAN.md U6): the privileged verifier lines of the
memory tree's lost episodes, for bit_propose.py --failed-tests. No replay: the lines come from the per-episode "rationale" (and
"rationale_diag" when the rationale is only "Validation called at turn i but nb_turns is n") logged by bos_gaia2.py.
Default lines (no oracle arguments, plan decision 5 / risk "privileged leakage"):
  ToolCallCountsFailure        -> "write calls of <tool>: agent <a>, oracle <o>" per tool, plus the AUI message-count lines verbatim
  OracleEventMatchingFailure   -> "oracle action <tool> not matched" (+ the matching-attempt reasons, without event ids)
  EnvOracleMatchingFailure     -> "an oracle environment/user event could not be matched (scenario or harness issue)"
--with-args (ablation) appends the oracle tool args ("  arg <k> = <v>", as logged by ARE, <= 200 chars each).
usage: python gaia2/g2_failed_checks.py --tree bit/R0/tree.json --runs gaia2/results/A.json,B.json --out bit/R0/failed_checks.json [--with-args]"""
import argparse, collections, json, os, re

_EARLY = re.compile(r"^Validation called at turn (\d+) but nb_turns is (\d+)")
_COUNT = re.compile(r"^- Tool '([^']*)': Agent count (\d+), Oracle count (\d+)\s*$")
_ATTEMPT = re.compile(r"reason:\s*(.+?)\s*$")


def _oracle_block(text, with_args):
    """OracleEventMatchingFailure text -> lines."""
    m = re.search(r"tool name:\s*(\S+)", text)
    lines = [f"oracle action {m.group(1) if m else '?'} not matched"]
    attempts = collections.Counter(_ATTEMPT.search(l).group(1) for l in text.split("List of matching attempts:", 1)[-1].splitlines()
                                   if l.startswith("-") and _ATTEMPT.search(l)) if "List of matching attempts:" in text else {}
    if attempts: lines[0] += " (agent calls tried: " + ", ".join(f"{r} x{n}" if n > 1 else r for r, n in sorted(attempts.items())) + ")"
    elif "List of matching attempts:" in text: lines[0] += " (no agent call of this tool to match)"
    if with_args:
        body = text.split("tool args:", 1)[1].split("List of matching attempts:", 1)[0] if "tool args:" in text else ""
        for l in body.strip("\n").splitlines():
            km = re.match(r"^-([^:]+):\s?(.*)$", l)
            if km: lines.append(f"  arg {km.group(1).strip()} = {km.group(2)}")
            elif l.strip() and len(lines) > 1: lines[-1] += " " + l.strip()   # a multi-line arg value
    return lines


def checks_from_rationale(rationale, diag=None, with_args=False):
    """official rationale (+ diagnostic rationale of the current turn) -> list of verifier lines; [] for a success / no rationale."""
    text = (rationale or "").strip(); out = []
    em = _EARLY.match(text)
    if em:
        out.append(f"the episode ended before its last turn (validation at turn {em.group(1)} of {em.group(2)})")
        text = (diag or "").strip()
    if not text: return out
    if "Agent and oracle counters do not match" in text or "more message(s) than agent" in text or "exceeds oracle AUI count" in text:
        for l in text.splitlines():
            l = l.strip(); cm = _COUNT.match(l)
            if cm: out.append(f"write calls of {cm.group(1)}: agent {cm.group(2)}, oracle {cm.group(3)}")
            elif l.startswith("Oracle sent ") or l.startswith("Agent message to user count"): out.append(l)
        return out
    if "Agent did not perform the following oracle tool call" in text: return out + _oracle_block(text, with_args)
    if text.startswith("Failure: Oracle env/user event"): return out + ["an oracle environment/user event could not be matched (scenario or harness issue)"]
    first = " ".join(text.split())[:200]
    return out + [f"verifier: {first}"]


def failed_checks(tree, runs, with_args=False, all_lost=False):
    """-> {eid: [lines]} for the tree's lost episodes (every lost, non-crashed episode of runs if all_lost)."""
    want = {c["lost"] for c in tree["cases"]} if tree else None; out = {}
    for p in [x for x in runs.split(",") if x] if isinstance(runs, str) else runs:
        d = json.load(open(p, encoding="utf-8")); n = len(d["games"])
        rat = d.get("rationale") or [None] * n; diag = d.get("rationale_diag") or [None] * n; cr = d.get("crashed") or [None] * n
        for i, (t, w) in enumerate(zip(d["games"], d["won"])):
            eid = f"{d['tag']}_s{d['seed']}:{t}"
            if w or cr[i] or (want is not None and not all_lost and eid not in want): continue
            out[eid] = checks_from_rationale(rat[i] if i < len(rat) else None, diag[i] if i < len(diag) else None, with_args)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tree", required=True); ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--with-args", action="store_true", help="ablation: keep the oracle tool args")
    ap.add_argument("--all-lost", action="store_true", help="every lost episode of --runs, not only the tree's cases"); a = ap.parse_args()
    out = failed_checks(json.load(open(a.tree, encoding="utf-8")), a.runs, a.with_args, a.all_lost)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for eid, ls in out.items(): print(eid, ls)
    print(f"{len(out)} episodes -> {a.out}")


if __name__ == "__main__":
    main()
