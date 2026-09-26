HISTORY_LENGTH = 15
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state.setdefault("observations", []).append(observation)
    state.setdefault("actions", []).append(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Track the frequency of previously visited states to switch the strategy if caught in a loop
    visit_count = {obs: state["observations"].count(obs) for obs in set(state["observations"])}
    if any(count > 2 for count in visit_count.values()):
        # Find the least repeated action in memory to reduce repetition
        action_frequencies = {act: state["actions"].count(act) for act in set(state["actions"])}
        fallback = min(action_frequencies, key=action_frequencies.get)
        if fallback.lower() in admissible:
            return fallback.lower()
    return "look"