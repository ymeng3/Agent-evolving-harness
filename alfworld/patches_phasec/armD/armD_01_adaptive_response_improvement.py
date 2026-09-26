HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r'<action>(.*?)</action>', response, re.DOTALL)
    action = match.group(1).strip() if match else ''
    return action.lower() if action.lower() in (a.lower() for a in admissible) else ''

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        if action not in admissible:  # When an inadmissible action was chosen
            extra_reasoning = "Please focus on the immediate task and available options. " if attempt == 1 else "Include the current admissible actions in your reasoning."
            state.setdefault('retries', 0)
            state['retries'] += 1
            return {"extra_instruction": extra_reasoning, "temperature": 0.3 + attempt * 0.1}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state['last_action'] = action

def choose_fallback(admissible: list[str], state: dict) -> str:
    state['fallback'] = state.get('fallback', 0) + 1
    return admissible[state['fallback'] % len(admissible)]