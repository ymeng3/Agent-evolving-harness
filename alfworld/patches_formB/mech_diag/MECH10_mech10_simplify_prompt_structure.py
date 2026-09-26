def format_prompt(prompt: str, state: dict) -> str:
    # Function to simplify the prompt by reducing excess structure and conciseness
    import re

    # Extract reasoning and action prompt section using regex
    reasoning_match = re.search(r"(Now it's your turn to take an action.*?)You should first reason step-by-step", prompt, re.DOTALL)
    if reasoning_match:
        reasoning_instruction = reasoning_match.group(1)
    else:
        reasoning_instruction = ""

    # Simplify the instructions
    simplified_instruction = ("Now decide an action for the current situation. "
                              "Think carefully then provide it inside <think> </think> and <action> </action> tags.")

    # Substitute the original reasoning instruction with the simplified one
    prompt = prompt.replace(reasoning_instruction, simplified_instruction)

    return prompt