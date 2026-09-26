HISTORY_LENGTH = 7
TEMPERATURE = 0.4

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Enhanced action extraction with an emphasis on admissibility
    def extract_action(text: str) -> str:
        # Match action within <action> tags
        match = re.search(r"<action>(.*?)<\/action>", text, re.IGNORECASE)
        if match:
            action = match.group(1).strip().lower()
            if action in admissible:
                return action
        # Match directly from response if <action> tags fail
        for action in admissible:
            if action in text.lower():
                return action
        # Default to 'look' if no valid action is found
        return "look"

    # Extract and return refined action
    return extract_action(response)

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Introduce memory to track past actions and outcomes
    if 'action_memory' not in state:
        state['action_memory'] = []
    state['action_memory'].append((action, next_observation))

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Add retry logic with adaptive changes based on past outcomes
    retry_instruction = "Ensure the next action is admissible and consider varying strategy if repeated actions are ineffective."
    if attempt == 1:
        return {"extra_instruction": retry_instruction, "temperature": 0.5}
    elif attempt == 2:
        # Check for repetitive failures and suggest a strategy change
        if len(state.get('action_memory', [])) > 1:
            last_action, last_outcome = state['action_memory'][-1]
            if last_action == action and "successfully" not in last_outcome:
                retry_instruction += " Avoid repeating recently failed action."
        return {"extra_instruction": retry_instruction, "temperature": 0.3}
    return None