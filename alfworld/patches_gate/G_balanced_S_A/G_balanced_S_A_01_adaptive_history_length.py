def format_prompt(prompt: str, state: dict) -> str:
    # Adjust the history length dynamically based on the task and progress within the episode.
    def compute_dynamic_history(step_count, default_length=5, task_weight=2):
        # This heuristic adjusts the history length based on step count and a fixed task weight.
        # More complex tasks may benefit from recalling a longer history as steps increase.
        return min(max(default_length, step_count // task_weight), 20)

    # Extract current step count from the prompt or use a fallback.
    import re
    step_match = re.search(r'at step (\d+)', prompt)
    step_count = int(step_match.group(1)) if step_match else 0
    
    # Calculate dynamic history length and apply it.
    dynamic_history_length = compute_dynamic_history(step_count)
    prompt = re.sub(r'most recent \d+ observations', f'most recent {dynamic_history_length} observations', prompt)

    return prompt