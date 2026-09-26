# P01 admissible-action snapping (ReAct/ALFWorld-standard "valid action projection"; also what most agent
# frameworks (AgentBoard, ExpeL code) do). In-episode only. Hook: parse_action.
import re
_clean = lambda s: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", re.sub(r"<[^>]+>", " ", s.lower()))).strip()
def parse_action(response, admissible, state):
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    cand = m[-1].strip().lower() if m else ""
    if cand in admissible: return cand
    if not cand:                                   # truncated / no tag: take last line that mentions an admissible verb
        lines = [l for l in response.lower().splitlines() if l.strip()]
        cand = _clean(lines[-1]) if lines else ""
    c = _clean(cand)
    for a in admissible:                            # exact after cleaning, then containment
        if _clean(a) == c: return a
    hits = [a for a in admissible if _clean(a) in c or c in _clean(a)]
    if len(hits) == 1: return hits[0]
    best = _closest(c, [_clean(a) for a in admissible])
    if best: return admissible[[_clean(a) for a in admissible].index(best[0])]
    return cand
_jac = lambda c, p: len(set(c.split()) & set(p.split())) / max(1, len(set(c.split()) | set(p.split())))   # difflib not importable
_closest = lambda c, pool, cutoff=0.75: [max(pool, key=lambda p: _jac(c, p))] if pool and max(_jac(c, p) for p in pool) >= cutoff else []
