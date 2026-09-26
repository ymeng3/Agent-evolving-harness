HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Ensure the instruction is clear and focused, emphasizing step-by-step reasoning
    instruction_focus = (
        "Remember to focus on the task at hand and the immediate surroundings. "
        "Make sure to utilize the recent observations effectively while reasoning."
    )
    return prompt + instruction_focus

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_match = re.search(r'<action>(.*?)</action>', response, re.IGNORECASE)
    if action_match:
        action = action_match.group(1).strip().lower()
        if action in admissible:
            return action
    return 'look'  # Fallback to a safe default action if parsing fails

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Maintain a simple memory to track previous actions and observations for enhanced decision-making
    state.setdefault('history', []).append((observation, action, next_observation))
    # Limit the length of stored history to avoid excessive memory usage
    if len(state['history']) > 20:
        state['history'].pop(0)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer a 'look' action if nothing better is found, ensuring exploration continues
    if 'look' in admissible:
        return 'look'
    return random.choice(admissible)