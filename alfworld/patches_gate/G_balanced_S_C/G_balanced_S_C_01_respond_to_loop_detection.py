import itertools

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "past_states" not in state:
        state["past_states"] = []

    current_state = (observation, action)
    state["past_states"].append(current_state)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    past_states = state.get("past_states", [])
    if len(past_states) >= 3:
        last_three = past_states[-3:]
        # Check if the last three states are the same, indicating a loop
        if len(set(last_three)) == 1:
            extra_instruction = (
                "It seems you might be stuck in a loop. Try to change your action strategy."
                " Consider different actions that might help progress towards the goal."
            )
            return {"extra_instruction": extra_instruction, "temperature": 0.5}
    return None