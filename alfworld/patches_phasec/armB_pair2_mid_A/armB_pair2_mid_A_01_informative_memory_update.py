HISTORY_LENGTH = 7
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": "Try to reason carefully and choose from the provided admissible actions.",
            "temperature": 0.5
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Focus on selecting actions distinctly different from previous attempts.",
            "temperature": 0.3
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    def is_interaction_action(action_text):
        return any(keyword in action_text for keyword in ["take", "put", "open", "close", "turn"])
    
    if "interaction_log" not in state:
        state["interaction_log"] = []
     
    if is_interaction_action(action):
        state["interaction_log"].append((action, observation))