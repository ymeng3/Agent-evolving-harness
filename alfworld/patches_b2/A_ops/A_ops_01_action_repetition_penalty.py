HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'repeated_actions' not in state:
        state['repeated_actions'] = set()
    state['repeated_actions'].add(action)

def format_prompt(prompt: str, state: dict) -> str:
    repeated_actions = state.get('repeated_actions', set())
    penalty_notice = ""
    if repeated_actions:
        penalty_notice = "You have repeated the following actions: " + ", ".join(repeated_actions) + ". Consider exploring different actions to achieve your goals."
    return prompt + ("\nNote: " + penalty_notice if penalty_notice else "")

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2 and action in state.get('repeated_actions', set()):
        extra_instruction = "Your previous action has been repeated multiple times without success. Explore different actions that are admissible."
        return {"extra_instruction": extra_instruction}
    return None