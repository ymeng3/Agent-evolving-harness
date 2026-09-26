HISTORY_LENGTH = 12
TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize visitation memory
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()

    # Record visited receptacles and their state
    receptacle_pattern = re.compile(r"(on|in|inside|at) the (\w+)")
    matches = receptacle_pattern.findall(next_observation.lower())
    for _, receptacle in matches:
        state["visited_receptacles"].add(receptacle)

import random

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Try to minimize repeated actions or revisit already visited receptacles
    unvisited_actions = [action for action in admissible if not any(receptacle in action for receptacle in state.get("visited_receptacles", []))]

    # If there's a suitable unvisited action, choose randomly from them; otherwise just select randomly from all admissible actions
    return random.choice(unvisited_actions if unvisited_actions else admissible)


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE - 0.1}
    return None