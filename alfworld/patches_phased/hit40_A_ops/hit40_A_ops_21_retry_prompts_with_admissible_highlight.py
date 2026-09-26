HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    def get_highlighted_prompt(admissible_actions: str) -> str:
        # Highlight new admissible actions to bring attention during invalid action retries
        highlighted_actions = ", ".join([f"**{action}**" for action in admissible_actions.split(", ")])
        return f"Make sure to choose among these admissible actions: {highlighted_actions}."

    # Add an introductory reminder on admissible actions to the prompt
    admissible_start_index = prompt.index("Your admissible actions of the current situation are:")
    admissible_end_index = prompt.index(".")

    highlighted_part = get_highlighted_prompt(prompt[admissible_start_index + len("Your admissible actions of the current situation are:"):admissible_end_index].strip())
    return prompt.replace(prompt[admissible_start_index:admissible_end_index], highlighted_part)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    base_instruction = "Your previous action was not admissible."
    extra_instruction = ""
    if attempt == 1:
        extra_instruction += f" {base_instruction} Please remember these are your options: "
    elif attempt == 2:
        extra_instruction += f" {base_instruction} It's important to select from these options now: "
        
    # Integrate this into the prompt if actions are available
    if admissible:
        extra_instruction += ", ".join([f"**{action}**" for action in admissible])

    return {"extra_instruction": extra_instruction}