def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'seen_observations' not in state:
        state['seen_observations'] = set()
    # Add current observation to seen observations
    state['seen_observations'].add(observation)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action wasn't admissible. "
            "Ensure the action matches one of the admissible actions."
        )
        # Check for repeated observations and adjust guidance if detected
        if len(state['seen_observations']) > 1 and observation in state['seen_observations']:
            extra_instruction += (
                " You seem to be encountering the same situation again. "
                "Consider actions that might progress you differently than before."
            )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    return None