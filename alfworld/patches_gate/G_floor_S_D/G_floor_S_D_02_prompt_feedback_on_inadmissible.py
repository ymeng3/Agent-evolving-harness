def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide context-sensitive feedback when an inadmissible action is selected, to guide the model towards valid actions.
    """
    def format_feedback(action_attempt):
        feedback_templates = [
            ("open", "Check if there's anything new to interact with after opening."),
            ("close", "Ensure you're successfully closing the object."),
            ("take", "Consider if the object is currently accessible for taking."),
            ("put", "Verify if the target receptacle is suitable and available."),
            ("heat", "Ensure the object can be heated properly in the situation."),
            ("cool", "Check if the cooling method is correct for this context."),
            ("clean", "Make sure the cleaning tools are present and useful."),
            ("look", "Be specific on what you need to observe for better decisions.")
        ]
        for keyword, feedback in feedback_templates:
            if keyword in action_attempt:
                return feedback
        return "Reassess the context and possible actions."

    if attempt < 2:
        feedback = format_feedback(action)
        return {
            "extra_instruction": f"Your last action was inadmissible. {feedback}. Focus on picking an admissible action.",
            "temperature": 0.3  # Slightly reduce temperature for a more focused response.
        }
    return None