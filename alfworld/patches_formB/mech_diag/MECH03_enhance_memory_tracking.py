from collections import defaultdict

HISTORY_LENGTH = 3
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Enhances memory to better track and limit revisits to receptacles.
    """
    if 'visited_receptacles' not in state:
        state['visited_receptacles'] = defaultdict(int)
    
    receptacle_locations = ('in the drawer', 'on the table', 'in the cabinet', 
                            'in the fridge', 'in the sink', 'on the counter')

    update_receptacle_visits = lambda loc: state['visited_receptacles'].update({loc: state['visited_receptacles'][loc] + 1})

    for location in receptacle_locations:
        if location in observation or location in next_observation:
            update_receptacle_visits(location)
            break

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    """
    Ensures action selection avoids revisiting overly revisited receptacles.
    """
    # Extract action from response
    start = response.find('<action>') + len('<action>')
    end = response.find('</action>', start)
    action = response[start:end].strip().lower()

    # If action is admissible and doesn't cause excessive revisits, proceed
    if action in admissible:
        for receptacle, count in state.get('visited_receptacles', {}).items():
            if receptacle in action and count >= 3:
                # Force a fallback to 'look' if abusing a receptacle
                return 'look'
        return action

    # Default fallback when action is not admissible
    return 'look'