HISTORY_LENGTH = 10
TEMPERATURE = 0.3
import math
import collections

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
        state['receptacle_revisit_counts'] = collections.defaultdict(int)
    for receptacle in state['visited_receptacles']:
        state['receptacle_revisit_counts'][receptacle] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        additional_instruction = "Be sure to select an action from the admissible actions list."
        return {"extra_instruction": additional_instruction, "temperature": TEMPERATURE}
    if attempt == 2:
        return {"temperature": TEMPERATURE}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Fallback strategy based on parity: if step is even, try 'look', if odd, randomly pick a valid action
    current_step = len(state['action_history'])
    return 'look' if current_step % 2 == 0 else random.choice(admissible)