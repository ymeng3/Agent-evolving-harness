# P08 positive-control STACK: snapping + brevity + retry + visited memory + loop-break. This is roughly what the
# 'ReAct with a competent action wrapper' baselines in 2606.28374 / 2607.21596 already contain. In-episode only.
import re, random, collections
HISTORY_LENGTH = 10
TEMPERATURE = 0.2
RULE = ("\n\nFORMAT: <think> at most 2 short sentences. Then exactly one action copied VERBATIM from the admissible list inside "
        "<action></action>, nothing after it.")
_clean = lambda s: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", re.sub(r"<[^>]+>", " ", s.lower()))).strip()
_act_of = lambda action: (lambda m: (m.group(1) if m else action).strip().lower())(re.search(r"<action>(.*?)</action>", action, re.S | re.I))
def format_prompt(prompt, state):
    v = state.get("visited", {}); note = ""
    if v: note += "\nMEMORY - already checked: " + "; ".join(f"{k}: {val}" for k, val in list(v.items())[-12:])
    if state.get("holding"): note += f"\nMEMORY - holding: {state['holding']}."
    if state.get("last_failed"): note += "\nNOTE - last action did nothing; do something different."
    return prompt.replace("Now it's your turn to take an action.", note + "\nNow it's your turn to take an action.") + RULE
def parse_action(response, admissible, state):
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I); cand = m[-1].strip().lower() if m else ""
    if not cand:
        lines = [l for l in response.lower().splitlines() if l.strip()]; cand = lines[-1] if lines else ""
    c = _clean(cand); act = cand
    if cand not in admissible:
        ex = [a for a in admissible if _clean(a) == c]; hits = ex or [a for a in admissible if _clean(a) in c or c in _clean(a)]
        if len(hits) == 1: act = hits[0]
        else:
            best, bs = None, 0.0; cs = set(c.split())
            for a in admissible:
                ps = set(_clean(a).split()); j = len(cs & ps) / max(1, len(cs | ps))
                if j > bs: best, bs = a, j
            if best and bs >= 0.75: act = best
    h = state.get("hist", []); noop = state.get("noop", {})
    if act in admissible and (noop.get(act, 0) >= 2 or (len(h) >= 2 and h[-1] == h[-2] == act)):
        alt = [a for a in admissible if a not in noop and a != act and a not in ("look", "inventory") and a not in h[-6:]]
        if alt: act = random.choice([a for a in alt if a.startswith("go to")] or alt)
    return act
def retry_policy(attempt, response, action, admissible, state):
    return {"extra_instruction": f"'{action[:60]}' is NOT admissible. Answer <think>brief</think><action>X</action> with X copied exactly from the list.",
            "temperature": 0.0 if attempt == 1 else 0.7}
def memory_update(state, observation, action, next_observation):
    act = _act_of(action); nxt = next_observation.lower(); state.setdefault("hist", []).append(act); state.setdefault("visited", {})
    if "nothing happens" in nxt: state.setdefault("noop", collections.Counter())[act] += 1
    g = re.match(r"(?:go to|open) (.+)", act)
    if g:
        found = re.findall(r"you see (.*?)(?:\.|$)", nxt); state["visited"][g.group(1)] = (found[0][:80] if found else "nothing")
    t = re.match(r"take (.+?) from", act)
    if t and "nothing happens" not in nxt: state["holding"] = t.group(1)
    if act.startswith("put ") and "nothing happens" not in nxt: state["holding"] = None
    state["last_failed"] = "nothing happens" in nxt
def choose_fallback(admissible, state):
    h = state.get("hist", []); alt = [a for a in admissible if a.startswith("go to") and a not in h]
    return random.choice(alt) if alt else "look"
