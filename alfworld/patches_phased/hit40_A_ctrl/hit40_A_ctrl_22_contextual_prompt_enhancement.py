HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    """ Enhance the prompt to provide additional context and guidance in the thinking process. """
    contextual_instruction = (
        "Focus on the current goal and available objects in the environment. "
        "Use logical reasoning based on past observations and actions."
    )
    modified_prompt = prompt.replace(
        "Now it's your turn to take an action.",
        contextual_instruction + " Now it's your turn to take an action."
    )
    return modified_prompt