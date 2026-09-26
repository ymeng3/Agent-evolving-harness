def format_prompt(prompt: str, state: dict) -> str:
    # Enhance the prompt with better separation and emphasis on critical instruction components.
    lines = prompt.split('\n')

    # Separate into sections
    task_line = lines[0]
    history_start_idx = 2
    history_end_idx = lines.index('Your admissible actions of the current situation are: [') - 1
    observation_idx = history_end_idx + 1
    admissible_idx = observation_idx + 1
    instruction_line = admissible_idx + 1

    # Capitalize and emphasize instruction to clarify thinking and action tags requirement.
    lines[instruction_line] = "YOU MUST FIRST REASON STEP-BY-STEP ABOUT THE CURRENT SITUATION. " + \
                              "THIS REASONING PROCESS MUST BE ENCLOSED WITHIN <THINK> </THINK> TAGS. " + \
                              "ONCE YOU'VE FINISHED YOUR REASONING, YOU SHOULD CHOOSE AN ADMISSIBLE ACTION AND PRESENT IT WITHIN <ACTION> </ACTION> TAGS."

    # Compile the revamped prompt
    return '\n'.join(lines)