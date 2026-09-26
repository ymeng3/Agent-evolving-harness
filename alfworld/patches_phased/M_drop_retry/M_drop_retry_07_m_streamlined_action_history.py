HISTORY_LENGTH = 10
from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize the state if not already done
    state.setdefault('visited_receptacles', set())
    state.setdefault('carried_objects', set())
    state.setdefault('action_history', [])
    state.setdefault('receptacle_revisit_counts', defaultdict(int))
    
    # Update visited receptacles
    if 'receptacle' in observation:
        state['visited_receptacles'].add(observation)
    
    # Update action history
    state['action_history'].append((observation, action))
    if len(state['action_history']) > HISTORY_LENGTH:
        state['action_history'].pop(0)
    
    # Update carried objects
    if 'take' in action:
        object_taken = action.split('take ')[1]
        state['carried_objects'].add(object_taken)
    if 'place' in action:
        object_placed = action.split('place ')[1]
        state['carried_objects'].discard(object_placed)
    
    # Update receptacle revisit counts
    for receptacle in state['visited_receptacles']:
        state['receptacle_revisit_counts'][receptacle] += 1