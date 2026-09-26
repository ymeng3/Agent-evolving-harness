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
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
    visited_receptacles_in_observation = set()

    def extract_receptacle_info(observation):
        words = observation.split()
        receptacles = [word for word in words if "receptacle" in word.lower()]
        return set(receptacles)

    visited_receptacles_in_observation.update(extract_receptacle_info(observation))
    visited_receptacles_in_observation.update(extract_receptacle_info(next_observation))

    # Update the state with newly visited receptacles
    state["visited_receptacles"].update(visited_receptacles_in_observation)