HISTORY_LENGTH = 10
TEMPERATURE = 0.5

from collections import defaultdict

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Re-examine the list of admissible actions and select the best fit for the current context."
    if attempt == 1:
        state["retry_count"] += 1
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        state["retry_count"] += 1
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory tracker on first call
    if "visited_objects" not in state:
        state["visited_objects"] = set()
        state["retry_count"] = 0

    # Track visited objects for optimization
    def extract_objects(observation: str):
        return set(word for word in observation.split() if word.isalnum())

    objects_in_view = extract_objects(observation)
    state["visited_objects"].update(objects_in_view)

    # If retries exceed threshold, take corrective measures in memory
    if state["retry_count"] > 3:
        state["visited_objects"].clear()  # Emulating refreshed outlook on environment

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Default to 'look' and track it in visited objects to avoid redundant actions
    if 'look' in admissible and 'look' not in state["visited_objects"]:
        return 'look'

    # If 'look' already visited, fallback to any other admissible action
    return next((action for action in admissible if action not in state["visited_objects"]), admissible[0])