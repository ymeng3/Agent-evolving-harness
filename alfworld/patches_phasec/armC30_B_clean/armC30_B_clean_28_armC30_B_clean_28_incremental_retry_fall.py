HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The action you selected was invalid. Focus on choosing a valid action from the list."
    retry_instructions = [
        {"extra_instruction": extra_instruction, "temperature": 0.6},
        {"extra_instruction": extra_instruction + " Be more attentive this time.", "temperature": 0.7}
    ]
    if attempt <= 2:
        return retry_instructions[attempt - 1]
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    prefer_simple_action = lambda action: action.startswith('look') or action.startswith('check')
    simple_actions = list(filter(prefer_simple_action, admissible))
    return simple_actions[0] if simple_actions else admissible[0]