HISTORY_LENGTH = 10
from collections import defaultdict
import re

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_receptacles' not in state:
        state['visited_receptacles'] = set()
        state['carried_objects'] = set()
        state['action_history'] = []
        state['observation_keywords'] = set()
    # Extract keywords from observations
    keywords = set(re.findall(r'\b[a-zA-Z]{3,}\b', observation))
    state['observation_keywords'].update(keywords)

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

def format_prompt(prompt: str, state: dict) -> str:
    # Emphasize dynamic observation handling
    observation_keywords = ', '.join(state.get('observation_keywords', []))
    enhanced_prompt = (
        f"You have noticed important details: {observation_keywords}. "
        "Utilize this information in your reasoning. "
    )
    return prompt + enhanced_prompt