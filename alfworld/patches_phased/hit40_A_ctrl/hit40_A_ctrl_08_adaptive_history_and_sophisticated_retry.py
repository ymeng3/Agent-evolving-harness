HISTORY_LENGTH = 8

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Enhanced extraction with fallback mechanisms
    import re
    # Try to extract the action within action tags
    match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    
    # Try to match any part of the response with the admissible actions (case insensitive)
    for action in admissible:
        if action in response.lower():
            return action
    
    # As a final fallback, choose a default action if the others fail
    return "look"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Implements a sophisticated retry strategy that adapts based on attempt number and response context.
    """
    if attempt == 1:
        # First retry: add targeted instruction and modify temperature
        return {
            "extra_instruction": "Ensure to select an action that is under the admissible actions.",
            "temperature": 0.45
        }
    elif attempt == 2:
        # Second retry: provide stronger directive and further adjust temperature
        return {
            "extra_instruction": "Critically choose from the admissible list only. Reflect on the task requirements.",
            "temperature": 0.35
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Implement adaptive history length dynamics or state-based logic
    if "step_memory" not in state:
        state["step_memory"] = []
    
    # Store current state
    state["step_memory"].append((observation, action))
    
    # Adaptively manage memory length
    if len(state["step_memory"]) > HISTORY_LENGTH:
        state["step_memory"].pop(0)