HISTORY_LENGTH = 7

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Enhance the storage of feedback based on success or failure of actions
    success_keywords = ['successfully', 'completed', 'achieved', 'done', 'progress']
    failure_keywords = ['failed', 'unable', 'cannot', 'missed', 'incorrect']
    
    def action_feedback(observation: str) -> str:
        if any(keyword in observation for keyword in success_keywords):
            return f"The last action '{action}' was effective. Consider this strategy."
        elif any(keyword in observation for keyword in failure_keywords):
            return f"The previous action ('{action}') didn't have the desired effect. Re-evaluate the strategy or objectives."
        return ""
    
    feedback = action_feedback(next_observation)
    if feedback:
        state['memory_feedback'] = feedback

def format_prompt(prompt: str, state: dict) -> str:
    # Add stored feedback from memory to assist the agent
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nNote: {memory_feedback}."
    return prompt