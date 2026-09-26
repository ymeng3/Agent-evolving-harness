HISTORY_LENGTH = 10
TEMPERATURE = 0.3

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update state with current observation and action
    if "visited_states" not in state:
        state["visited_states"] = set()
    state["visited_states"].add((observation, action))

    # Track occurrences of each action to detect repeated action pattern
    if "action_count" not in state:
        state["action_count"] = {}

    if action not in state["action_count"]:
        state["action_count"][action] = 0
    state["action_count"][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        extra_instruction = "Please reconsider. Choose an action from the admissible list carefully."
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None


import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Define a helper function to clean and refine the extracted action
    def extract_action(text: str) -> str:
        # Search for the first action enclosed in <action> tags with a more forgiving pattern
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        # If no valid match is found within tags, attempt to match actions directly from the text
        for action in admissible:
            if action in text.lower():
                return action
        
        # Default return if none match
        return "look"

    # Extract and return the refined action
    return extract_action(response)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Attempt to avoid previously repeated actions by selecting an action not overused.
    if "action_count" in state:
        sorted_actions = sorted(state["action_count"].items(), key=lambda x: x[1])
        for action, count in sorted_actions:
            if action in admissible and count < 3:
                return action

    # Default to selecting the first admissible action
    return admissible[0]