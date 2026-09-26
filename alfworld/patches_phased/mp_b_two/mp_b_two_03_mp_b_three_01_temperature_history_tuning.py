HISTORY_LENGTH = 15
TEMPERATURE = 0.45

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Ensure you select one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None

def memory_update(state, observation, action, next_observation):
    def extract_action(action_str):
        m = re.search(r"<action>(.*?)</action>", action_str, re.S | re.I)
        return (m.group(1) if m else action_str).strip().lower()
    
    act = extract_action(action)
    state.setdefault("action_history", []).append(act)
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop_counter", collections.Counter())[act] += 1

def parse_action(response, admissible, state):
    def extract_action(response_str):
        m = re.findall(r"<action>(.*?)</action>", response_str, re.S | re.I)
        return m[-1].strip().lower() if m else response_str.strip().lower()[-30:]
    
    act = extract_action(response)
    history = state.get("action_history", [])
    noop_counts = state.get("noop_counter", {})
    
    if act in admissible and (noop_counts.get(act, 0) >= 2 or (len(history) >= 2 and history[-1] == history[-2] == act)):
        state["loop_breaks"] = state.get("loop_breaks", 0) + 1
        alternatives = [a for a in admissible if a not in noop_counts and a != act and a != "look" and a != "inventory" and a not in history[-6:]]
        if alternatives:
            return random.choice([a for a in alternatives if a.startswith("go to")] or alternatives)
    
    return act

def choose_fallback(admissible, state):
    history = state.get("action_history", [])
    go_to_alternatives = [a for a in admissible if a.startswith("go to") and a not in history]
    return random.choice(go_to_alternatives) if go_to_alternatives else "look"