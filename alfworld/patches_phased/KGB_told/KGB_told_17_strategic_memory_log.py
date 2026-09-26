HISTORY_LENGTH = 10
TEMPERATURE = 0.35

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory if not present
    if "logged_actions" not in state:
        state["logged_actions"] = set()
    
    # Log the action if it's 'look' or 'examine' type of action to avoid repetitive observations
    if action.startswith("look") or action.startswith("examine"):
        state["logged_actions"].add(action)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Check if the action has been logged, indicating a potential repetitive move
    if action in state.get("logged_actions", set()):
        # Provide specific instruction to prevent repeating logged actions
        extra_instruction = "Avoid previously ineffective 'look' or 'examine' actions unless critical."
    else:
        # Generic instruction on invalid action
        extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."

    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": "Double-check the admissible actions and ensure they are relevant to the current stage.", "temperature": 0.45}
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