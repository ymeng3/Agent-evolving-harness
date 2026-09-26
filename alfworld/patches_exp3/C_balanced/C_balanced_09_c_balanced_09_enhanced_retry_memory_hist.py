HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Helper function for action extraction
    def extract_action(text: str) -> str:
        match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if match:
            action = match.group(1).strip().lower()
            if action in admissible:
                return action
        
        for action in admissible:
            if action in text.lower():
                return action
        
        return "look"
    
    action = extract_action(response)
    if 'action_count' not in state:
        state['action_count'] = {}
    state['action_count'].setdefault(action, 0)
    state['action_count'][action] += 1
    return action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Focus on selecting an action from the admissible list."
    if attempt == 1:
        if state['action_count'].get(action, 0) >= 3:
            admissible = [a for a in admissible if a != action]
            extra_instruction += " Avoid repeating the same action."
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    if state.get('action_count', {}).get('look', 0) >= 3:
        prompt = prompt.replace("current situation.", "current situation. Consider alternatives to simply 'look'.")
    return prompt