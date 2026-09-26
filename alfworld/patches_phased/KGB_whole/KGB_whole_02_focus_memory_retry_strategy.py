HISTORY_LENGTH = 8
TEMPERATURE = 0.5


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = (
        "Your last action was not valid. Please select the most suitable action from the admissible actions listed."
        " Consider the task requirements and your previous actions."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None


import re
import random


def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Helper to clean the action
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        # Attempt to select an admissible action using random choice to add variability in non-tag matches
        possible_matches = [action for action in admissible if action in text.lower()]
        if possible_matches:
            return random.choice(possible_matches)

        return "look"

    return extract_action(response)


def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited" not in state:
        state["visited"] = set()

    # Log visited rooms or significant identifiers from the observation
    rooms = {"kitchen", "bathroom", "bedroom", "living room"}
    for room in rooms:
        if room in observation:
            state["visited"].add(room)
            break


def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer unvisited significant rooms if applicable
    for room in state.get("visited", set()):
        try:
            admissible.remove(room)
        except ValueError:
            continue
    
    return random.choice(admissible)