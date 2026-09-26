HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Reason carefully and ensure you're considering the environment context."
            " Remember to avoid repeating previous mistakes."
        )
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state.setdefault("recent_actions", collections.deque(maxlen=HISTORY_LENGTH)).append(action)