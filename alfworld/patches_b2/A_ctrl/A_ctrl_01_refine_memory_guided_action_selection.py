from collections import deque

HISTORY_LENGTH = 7

def format_prompt(prompt: str, state: dict) -> str:
    memory_notes = " ".join(state.get("visited", []))
    if memory_notes:
        prompt += f"\nPreviously noted locations: {memory_notes}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re

    # Extract action using regex
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    
    # If parsing fails, default to 'look'
    return "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited' not in state:
        state['visited'] = deque(maxlen=10)
    # Add locations or interesting terms from observation to memory
    for term in ["kitchen", "living room", "bedroom", "object", "receptacle"]:
        if term in observation.lower() and term not in state['visited']:
            state['visited'].append(term)