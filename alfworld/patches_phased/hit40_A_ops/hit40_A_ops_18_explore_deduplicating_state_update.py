HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    prompt += "\nEnsure actions are diverse and within context."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_states' not in state:
        state['visited_states'] = set()
    current_state = (observation.strip().lower(), action)
    state['visited_states'].add(current_state)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": (
                "The previous action was invalid or a repetition of a previous state. "
                "Focus on selecting a unique and context-appropriate action."
            ),
            "temperature": 0.3
        }
    if attempt == 2:
        return {
            "extra_instruction": (
                "It's crucial to explore new actions. Consider your observations carefully."
            ),
            "temperature": 0.35
        }
    return None