import re

HISTORY_LENGTH = 10
TEMPERATURE = 0.3

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

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
    # Assuming receptacles are mentioned in observations starting with "receptacle: "
    receptacle_match = re.search(r"receptacle:\s*(\w+)", observation, re.IGNORECASE)
    if receptacle_match:
        receptacle = receptacle_match.group(1).lower()
        state["visited_receptacles"].add(receptacle)
    # Track last three actions to detect repetitive actions
    if "last_actions" not in state:
        state["last_actions"] = []
    state["last_actions"].append(action)
    if len(state["last_actions"]) > 3:
        state["last_actions"].pop(0)