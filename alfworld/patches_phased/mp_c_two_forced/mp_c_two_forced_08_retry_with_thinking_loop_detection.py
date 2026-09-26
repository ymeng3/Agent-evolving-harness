HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Add an emphasis on thinking thoroughly, derived from loop detection strategy
    emphasis = (
        " Remember to consider the context and avoid repeating actions that previously did not alter the environment."
    )
    return prompt + emphasis

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Retry policy temperature adjustments from A
    extra_instruction = (
        "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state, observation, action, next_observation):
    # Loop detection from B
    import re, collections

    m = re.search(r"<action>(.*?)</action>", action, re.S | re.I)
    act = (m.group(1) if m else action).strip().lower()
    state.setdefault("hist", []).append(act)
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop", collections.Counter())[act] += 1

def parse_action(response, admissible, state):
    # Loop breaking strategy from B
    import re, random

    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = m[-1].strip().lower() if m else response.strip().lower()[-30:]
    h = state.get("hist", [])
    noop = state.get("noop", {})
    if (
        act in admissible
        and (noop.get(act, 0) >= 2 or (len(h) >= 2 and h[-1] == h[-2] == act))
    ):
        state["loop_breaks"] = state.get("loop_breaks", 0) + 1
        alt = [
            a
            for a in admissible
            if a not in noop and a != act and a != "look" and a != "inventory" and a not in h[-6:]
        ]
        if alt:
            return random.choice([a for a in alt if a.startswith("go to")] or alt)
    return act

def choose_fallback(admissible, state):
    # Enhanced fallback from B
    import random

    h = state.get("hist", [])
    alt = [a for a in admissible if a.startswith("go to") and a not in h]
    return random.choice(alt) if alt else "look"