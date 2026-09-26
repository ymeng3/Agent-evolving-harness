HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    # Modify the prompt to include reminders about previously visited locations
    if 'revisits' in state:
        revisit_info = ' '.join(state['revisits'])
        prompt += f" Remember, you have already visited: {revisit_info}. Plan your next action accordingly."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Create a revisits list in the state if it doesn't exist
    if 'revisits' not in state:
        state['revisits'] = []

    # Check if the action involves moving to a location (contains 'go to' or 'move to')
    if 'go to' in action or 'move to' in action:
        location_name = action.split()[-1]  # Assume the last word is the location
        state['revisits'].append(location_name)

        # Limit the amount of stored revisits to avoid prompt overload
        if len(state['revisits']) > 5:
            state['revisits'].pop(0)