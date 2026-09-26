HISTORY_LENGTH = 10
from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_receptacles' not in state:
        state['visited_receptacles'] = set()
        state['carried_objects'] = set()
        state['action_history'] = []
    if 'receptacle' in observation:
        state['visited_receptacles'].add(observation)
    state['action_history'].append((observation, action))
    if 'take' in action:
        object_taken = action.split('take ')[1]
        state['carried_objects'].add(object_taken)
    if 'place' in action:
        object_placed = action.split('place ')[1]
        if object_placed in state['carried_objects']:
            state['carried_objects'].remove(object_placed)
    if 'receptacle_revisit_counts' not in state:
        state['receptacle_revisit_counts'] = defaultdict(int)
    for receptacle in state['visited_receptacles']:
        state['receptacle_revisit_counts'][receptacle] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Implement a strategic retry policy
    if attempt == 1:
        # First retry, hint at a more directed instruction
        return {"extra_instruction": "Ensure the action is relevant and appropriate to the objects in view."}
    elif attempt == 2:
        # Second retry, suggest focusing on carrying or placing actions
        return {"extra_instruction": "Consider focusing on 'take' or 'place' actions if applicable."}
    return None