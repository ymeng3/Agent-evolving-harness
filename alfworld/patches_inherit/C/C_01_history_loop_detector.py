HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "history" not in state:
        state["history"] = collections.deque(maxlen=10)
    state["history"].append((observation, action))

def choose_fallback(admissible: list[str], state: dict) -> str:
    index_counter = collections.defaultdict(int)
    pattern_counter = collections.defaultdict(int)
    
    # Identifying possible repetitive actions
    for idx, entry in enumerate(state.get("history", [])):
        key = (entry[0], entry[1])
        index_counter[key] = idx
        pattern_counter[key] += 1
    
    # Detect loops or repeated patterns
    max_pattern = max(pattern_counter.values(), default=0)
    if max_pattern > 1: 
        most_common_entry = max(pattern_counter, key=lambda x: pattern_counter[x])
        last_idx = index_counter[most_common_entry]
        follow_up_action = state["history"][last_idx + 1][1] if last_idx + 1 < 10 else None
        if follow_up_action and follow_up_action in admissible:
            return follow_up_action

    # Default fallback strategy
    return 'look'