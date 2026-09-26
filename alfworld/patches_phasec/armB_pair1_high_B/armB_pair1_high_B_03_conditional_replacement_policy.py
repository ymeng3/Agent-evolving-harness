import re, random, collections

HISTORY_LENGTH = 8
TEMPERATURE = 0.3

def memory_update(state, observation, action, next_observation):
    get_act = lambda act: (re.search(r"<action>(.*?)</action>", act, re.S | re.I).group(1) if "<action>" in act else act).strip().lower()
    act = get_act(action)
    state.setdefault("hist", []).append(act)
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop", collections.Counter())[act] += 1

def parse_action(response, admissible, state):
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = m[-1].strip().lower() if m else response.strip().lower()[-30:]
    h = state.get("hist", [])
    noop = state.get("noop", {})
    recent_repeat = len(h) >= 2 and h[-1] == h[-2] == act
    if act in admissible and (noop.get(act, 0) >= 2 or recent_repeat):
        alternatives = [a for a in admissible if a not in noop and a != act and a != "look" and a != "inventory" and a not in h[-6:]]
        for a in alternatives:
            if a.startswith("open") or a.startswith("examine"):
                return a
        if recent_repeat:
            conditionals = {"open": "go to", "examine": "inspect", "look": "search"}
            for prefix, conditional in conditionals.items():
                replacement_options = [a for a in alternatives if a.startswith(conditional)]
                if replacement_options:
                    return random.choice(replacement_options)
        if alternatives:
            return random.choice(alternatives)
    return act

def choose_fallback(admissible, state):
    h = state.get("hist", [])
    alternative = [a for a in admissible if a.startswith("go to") and a not in h]
    return random.choice(alternative) if alternative else "look"