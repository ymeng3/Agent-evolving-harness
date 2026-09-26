def format_prompt(prompt: str, state: dict) -> str:
    # Append a clarification to the prompt to mitigate confusion about the 'look' action
    clarification_note = (
        "\n\nSpecial Note: Use 'look' to gather more information about your surroundings when needed. "
        "Ensure this action is chosen with the context of exploration in mind, "
        "particularly if you are unsure of what to do next."
    )
    return prompt + clarification_note