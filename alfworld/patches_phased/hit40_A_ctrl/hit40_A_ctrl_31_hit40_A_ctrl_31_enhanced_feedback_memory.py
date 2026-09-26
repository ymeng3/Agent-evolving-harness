HISTORY_LENGTH = 6

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory state if not present
    if 'feedback' not in state:
        state['feedback'] = []

    # Store relevant feedback information in memory based on the action outcome
    success_indicators = ["successfully", "completed", "achieved"]
    obstacle_indicators = ["cannot", "blocked", "nothing happens"]

    # Determine if the action was successful or encountered an obstacle
    if any(indicator in next_observation for indicator in success_indicators):
        state['feedback'].append(f"Action '{action}' was successful.")
    elif any(indicator in next_observation for indicator in obstacle_indicators):
        state['feedback'].append(f"Action '{action}' ran into an issue.")

    # Limit feedback history to avoid excessive memory usage
    if len(state['feedback']) > 10:
        state['feedback'].pop(0)

def format_prompt(prompt: str, state: dict) -> str:
    # Append memory feedback to the prompt to provide additional context derived from previous actions
    memory_feedback = " ".join(state.get('feedback', []))
    
    if memory_feedback:
        prompt += f" Remember previous feedback: {memory_feedback}."
    
    return prompt