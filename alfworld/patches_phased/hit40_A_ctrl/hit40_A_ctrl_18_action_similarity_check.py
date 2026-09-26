import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Define a helper function to clean and refine the extracted action
    def extract_action(text: str) -> str:
        # Search for the first action enclosed in <action> tags
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action

        # If no valid match is found within tags, attempt to match actions directly from the text
        for action in admissible:
            if action in text.lower():
                return action

        # Default return if none match
        return "look"

    # Extract and return the refined action
    selected_action = extract_action(response)

    # Calculate the similarity score and select action with the highest similarity
    def calculate_similarity(action1: str, action2: str) -> float:
        # Simple similarity based on common characters (customize this function as needed)
        return sum(1 for a, b in zip(action1, action2) if a == b) / max(len(action1), len(action2))
    
    # Retry if selected action is not in admissible actions
    if selected_action not in admissible:
        highest_similarity, most_similar_action = -1, "look"
        for action in admissible:
            similarity = calculate_similarity(selected_action, action)
            if similarity > highest_similarity:
                highest_similarity, most_similar_action = similarity, action

        return most_similar_action

    return selected_action