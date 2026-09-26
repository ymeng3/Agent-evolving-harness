HISTORY_LENGTH = 8
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    # Integrate a summary of visited locations to improve memory management
    visited_summary = state.get("visited_summary", "")
    if visited_summary:
        prompt += f"\nRemember where you've been: {visited_summary}."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track visited locations to prevent revisits
    if 'visited' not in state:
        state['visited'] = set()
    if 'visited_summary' not in state:
        state['visited_summary'] = ""
    
    # Simple extractor to identify location names in observations
    def extract_location(obs: str) -> str:
        parts = obs.split()
        return next((part for part in parts if part.istitle()), "")

    location = extract_location(observation)
    if location and location not in state['visited']:
        state['visited'].add(location)
        state['visited_summary'] += f" {location}"

    # Update summary with unique visited locations
    state['visited_summary'] = ". ".join(state['visited']).strip()