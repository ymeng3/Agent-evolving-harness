HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": "Review the suggested action and ensure it matches one of the admissible actions accurately."
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Focus on selecting the most relevant action from the admissible list, considering the task context.",
            "temperature": 0.4
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'suggested_actions' not in state:
        state['suggested_actions'] = set()
    if action not in state['suggested_actions']:
        state['suggested_actions'].add(action)