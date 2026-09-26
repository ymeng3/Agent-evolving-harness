import re

HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Add info about invalid attempts to state memory
    state['invalid_attempts'] = state.get('invalid_attempts', 0) + 1
    
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

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

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory state
    if 'visited_positions' not in state:
        state['visited_positions'] = set()
    if 'repeated_actions' not in state:
        state['repeated_actions'] = 0

    # Track visited observations
    state['visited_positions'].add(next_observation)

    # Detect loops by counting repeated actions
    if action in state.get('last_actions', []):
        state['repeated_actions'] += 1
    else:
        state['repeated_actions'] = 0

    # Update last actions
    state['last_actions'] = state.get('last_actions', [])[-4:] + [action]
    
    # Declare a loop if we hit 3 repeated actions
    if state['repeated_actions'] >= 3:
        state['loop_detected'] = True
    else:
        state['loop_detected'] = False