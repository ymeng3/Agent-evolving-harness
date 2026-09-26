HISTORY_LENGTH = 10
from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory structures if not already done
    if 'visited_receptacles' not in state:
        state['visited_receptacles'] = set()
        state['carried_objects'] = set()
    if 'action_history' not in state:
        state['action_history'] = []
    if 'receptacle_revisit_counts' not in state:
        state['receptacle_revisit_counts'] = defaultdict(int)

    # Update visited receptacles
    if 'receptacle' in observation:
        state['visited_receptacles'].add(observation)

    # Update action history with the current (observation, action) pair
    state['action_history'].append((observation, action))

    # Manage carried objects based on actions taken
    if action.startswith('take'):
        object_taken = action.split('take ')[1]
        state['carried_objects'].add(object_taken)
    elif action.startswith('place'):
        object_placed = action.split('place ')[1]
        state['carried_objects'].discard(object_placed)

    # Increment revisit counts for all visited receptacles
    for receptacle in state['visited_receptacles']:
        state['receptacle_revisit_counts'][receptacle] += 1