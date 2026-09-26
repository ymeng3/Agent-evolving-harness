import random
from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track the frequency of each action taken to detect fixation
    if "action_counts" not in state:
        state["action_counts"] = defaultdict(int)
    
    state["action_counts"][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # If the same action is attempted too often, provide additional instructions
    action_counts = state.get("action_counts", {})
    
    if attempt == 1 and action_counts[action] > 2:
        # Randomize the choice of instruction to add variation and potentially disrupt fixation
        instructions = [
            "You've attempted this action multiple times. Consider exploring other options.",
            "This action is repeating too frequently. Try evaluating the environment for other possible actions.",
            "Reassess the situation; perhaps a different action could be more effective.",
        ]
        return {"extra_instruction": random.choice(instructions)}
    
    return None