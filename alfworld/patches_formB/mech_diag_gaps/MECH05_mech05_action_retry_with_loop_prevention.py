from collections import deque

HISTORY_LENGTH = 5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if "invalid_attempts" not in state:
        state["invalid_attempts"] = deque(maxlen=HISTORY_LENGTH)

    # Add attempt to the queue
    state["invalid_attempts"].append(action)

    # Check for potential loops (e.g., AAA or ABAB patterns)
    def has_loop(actions):
        if len(actions) < 3:
            return False
        last_action = actions[-1]
        if actions.count(last_action) > 1:
            return True
        if len(actions) % 2 == 0 and actions[:len(actions)//2] == actions[len(actions)//2:]:
            return True
        return False

    # Prevent immediate retry of the same or oscillating actions
    if has_loop(state["invalid_attempts"]):
        return {"extra_instruction": "Avoid repeating the same actions.", "temperature": 0.5}
    
    return {"temperature": 0.4}