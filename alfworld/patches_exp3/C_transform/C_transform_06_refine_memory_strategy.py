HISTORY_LENGTH = 5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize visited locations in state if not present
    if 'visited_locations' not in state:
        state['visited_locations'] = set()

    # Add current observation to visited locations
    state['visited_locations'].add(observation)

    # If the action is successful, update the feedback in state memory
    if "successfully" in next_observation:
        state["memory_feedback"] = f"The action '{action}' successfully changed the state."
    elif "cannot" in next_observation:
        state["memory_feedback"] = f"Action '{action}' was not effective. Try a different approach."

def format_prompt(prompt: str, state: dict) -> str:
    # Add memory of visited locations and feedback to the prompt
    visited_info = "You have visited: " + ', '.join(state.get('visited_locations', []))
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nRemember: {memory_feedback}. {visited_info}."
    else:
        prompt += f"\n{visited_info}."
    return prompt

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Check if there's a memory feedback about ineffectiveness and avoid choosing the same action
    feedback = state.get("memory_feedback", "")
    ineffective_action = None
    if "not effective" in feedback:
        ineffective_action = feedback.split("'")[1]
    # Pick an admissible action that isn't the ineffective one, defaulting to 'look' if all others are ineffective
    for action in admissible:
        if action != ineffective_action:
            return action
    return "look"