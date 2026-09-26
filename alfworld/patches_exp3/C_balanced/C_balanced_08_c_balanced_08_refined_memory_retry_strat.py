HISTORY_LENGTH = 7
TEMPERATURE = 0.4

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
    if 'action_count' not in state:
        state['action_count'] = {}
    if action not in state['action_count']:
        state['action_count'][action] = 0
    state['action_count'][action] += 1

    # Implement simple memory feedback
    if "successfully" in next_observation:
        state.pop('memory_feedback', None)  # Clear feedback on success
    else:
        state['memory_feedback'] = f"Last action '{action}' may need revision."

def format_prompt(prompt: str, state: dict) -> str:
    # Add a memory feedback to the prompt
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nNote: {memory_feedback}."
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        instruction = " The previous action was invalid. "
        if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
            admissible = [a for a in admissible if a != action]
            instruction += "Avoid repeating actions excessively. "
        if admissible:
            instruction += f"Choose an action different from: {action}."
        return {"extra_instruction": instruction, "temperature": 0.35}
    return None