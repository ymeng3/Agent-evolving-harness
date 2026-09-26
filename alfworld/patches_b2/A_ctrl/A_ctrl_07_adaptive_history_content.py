HISTORY_LENGTH = 5

def format_prompt(prompt: str, state: dict) -> str:
    # Extract observation history to analyze previous actions and adjust the prompt content
    observation_history = prompt.split("your current observation is:")[0]
    
    # Use observation contents to adjust the history included in the prompt
    if "<think>" not in observation_history or "failure" in observation_history.lower():
        # Reduce history if thinking was skipped or failures were detected
        history_trimmed = "\n".join(observation_history.splitlines()[-2:])
        prompt = prompt.replace(observation_history, history_trimmed)
    return prompt