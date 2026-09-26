HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    if not state.get("initialized"):
        state["initialized"] = True
        state["visited_objects"] = set()
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Extract and track objects mentioned in observations
    find_objects = lambda text: set(part.strip() for part in text.split() if part.strip().isalpha())
    observed_objects = find_objects(observation)
    state["visited_objects"].update(observed_objects)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    return None