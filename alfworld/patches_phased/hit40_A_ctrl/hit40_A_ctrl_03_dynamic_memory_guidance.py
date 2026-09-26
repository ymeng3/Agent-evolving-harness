HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Integrate dynamic memory guidance into the prompt based on previous steps
    def generate_memory_guidance(state):
        if 'visited_locations' in state and state['visited_locations']:
            last_visited = state['visited_locations'][-1]
            return f"Last visited location: {last_visited}."
        return ""
    
    memory_feedback = generate_memory_guidance(state)
    if memory_feedback:
        prompt += f"\nMemory Guidance: {memory_feedback}"
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Record visited locations for dynamic guidance
    if "location:" in observation:
        location = observation.split("location:")[1].strip()
        if 'visited_locations' not in state:
            state['visited_locations'] = []
        if location not in state['visited_locations']:
            state['visited_locations'].append(location)