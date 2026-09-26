HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "action_sequence" not in state:
        state["action_sequence"] = []
    state["action_sequence"].append(action)
    
    def check_pattern(sequence):
        pattern_correlations = [
            (["open fridge", "pick up apple"], "You're likely trying to 'store' the apple, so 'close fridge' may not follow.")
        ]
        for pattern, message in pattern_correlations:
            if sequence[-len(pattern):] == pattern:
                print(f"Pattern hint: {message}")
    
    check_pattern(state["action_sequence"])