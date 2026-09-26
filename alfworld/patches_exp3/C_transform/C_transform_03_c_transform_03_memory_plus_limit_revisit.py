HISTORY_LENGTH = 10

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory trackers if not present
    if 'visited_objects' not in state:
        state['visited_objects'] = set()
    if 'receptacle_count' not in state:
        state['receptacle_count'] = {}

    # Update visited objects and receptacle visit count
    state['visited_objects'].add(observation)
    if action.startswith("open") or action.startswith("search"):
        if action not in state['receptacle_count']:
            state['receptacle_count'][action] = 0
        state['receptacle_count'][action] += 1

def format_prompt(prompt: str, state: dict) -> str:
    # Add memory feedback and instruct agent to avoid rechecking the same receptacles excessively
    feedback = []
    
    # Add reminders for visited objects
    if state.get('visited_objects'):
        feedback.append(f"Remember you've already seen: {', '.join(state['visited_objects'])}.")
    
    # Limit receptacle revisits
    frequent_receptacles = [action for action, count in state.get('receptacle_count', {}).items() if count > 1]
    if frequent_receptacles:
        feedback.append(f"Avoid excessive revisits: {', '.join(frequent_receptacles)}.")

    # Append feedback to the prompt
    if feedback:
        prompt += "\n" + " ".join(feedback)
    
    return prompt