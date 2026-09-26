def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize or update the action memory to track inadmissible actions
    if 'inadmissible_actions' not in state:
        state['inadmissible_actions'] = set()
    if action not in state['inadmissible_actions']:
        state['inadmissible_actions'].add(action)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        inadvisables = state.get('inadmissible_actions', set())
        # Create a filtered list of admissible actions that weren't inadvisibly chosen previously
        filtered_admissible = [a for a in admissible if a not in inadvisables]
        
        if filtered_admissible:
            extra_instruction = (
                "Avoid choosing previously inadmissible actions. Carefully select from the remaining admissible actions."
            )
            return {"extra_instruction": extra_instruction}
        
    # On retry attempts, if no actions have been filtered out, proceed normally
    return {"temperature": 0.3}