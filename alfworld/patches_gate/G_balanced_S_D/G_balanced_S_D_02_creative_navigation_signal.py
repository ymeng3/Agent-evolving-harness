def format_prompt(prompt: str, state: dict) -> str:
    # Insert a creative signal to remind the model to focus on exploring new actions or paths
    exploration_signal = (
        "Consider possibly overlooked paths or actions that might lead to success. "
        "Use creative strategies to navigate the environment and achieve the goal while staying within admissible limits."
    )
    # Append the exploration signal to the original prompt
    return prompt + "\n" + exploration_signal