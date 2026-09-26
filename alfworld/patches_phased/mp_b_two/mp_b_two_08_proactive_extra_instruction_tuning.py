HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = (
        "The action you chose was not valid. Please carefully review the list of admissible actions "
        "and select from them while considering the task's context and history of actions."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state, observation, action, next_observation):
    m = re.search(r"<action>(.*?)</action>", action, re.S | re.I); act = (m.group(1) if m else action).strip().lower()
    state.setdefault("action_history", []).append(act)
    if "nothing happens" in next_observation.lower(): 
        state.setdefault("ineffective_actions", collections.Counter())[act] += 1

def parse_action(response, admissible, state):
    m = re.search(r"<action>(.*?)</action>", response, re.S | re.I)
    act = (m.group(1) if m else response).strip().lower()
    ineffective_actions = state.get("ineffective_actions", {})
    if act in admissible and ineffective_actions.get(act, 0) >= 2:
        alternatives = [a for a in admissible if ineffective_actions.get(a, 0) < 2 and a != act]
        return random.choice(alternatives) if alternatives else act
    return act