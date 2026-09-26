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

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Avoid revisiting receptacles if alternatives are available
    if state.get('receptacle_revisit_counts'):
        receptacle_visits = state['receptacle_revisit_counts']
        # Sort actions based on the frequency of visited receptacles or prefer non-receptacle actions
        admissible_sorted = sorted(
            admissible, 
            key=lambda act: receptacle_visits.get(act, 0) if 'receptacle' in act else -1
        )
        return admissible_sorted[0]
    return 'look'