HISTORY_LENGTH = 15
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    state.setdefault("step_count", 0)
    state["step_count"] += 1
    if state["step_count"] > 10:
        additional_info = "Remember, prioritize actions that move towards achieving the main goal and avoid redundant actions."
        prompt += "\n" + additional_info
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The chosen action was invalid. Please select only from the listed admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = m[-1].strip().lower() if m else response.strip().lower()
    if act not in admissible:
        if len(state.get("recent_invalid", [])) >= 3:
            last_valid = state["recent_invalid"][-1]
            alt = [a for a in admissible if a != last_valid]
            return random.choice(alt) if alt else "look"
        state.setdefault("recent_invalid", []).append(act)
    return act

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state.setdefault("hist", []).append(action)
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop", collections.Counter())[action] += 1

def choose_fallback(admissible: list[str], state: dict) -> str:
    h = state.get("hist", [])
    alt = [a for a in admissible if "go to" in a and a not in h]
    return random.choice(alt) if alt else "look"