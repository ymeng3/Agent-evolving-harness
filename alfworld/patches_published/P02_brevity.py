# P02 think-brevity / output-format control. Addresses F0's dominant failure: 512-token responses that never reach
# <action> (smoke traj shows '\ntherefore, the best next step' being executed). Cf. ReAct 'think' should be short;
# AgentTuning/AgentBoard format instructions. In-episode only. Hook: format_prompt.
FORMAT_RULE = ("\n\nIMPORTANT FORMAT RULES: keep your <think> to at most 2 short sentences (under 40 words). "
               "Then output exactly one admissible action, copied VERBATIM from the list above, inside <action></action>. "
               "Do not write anything after </action>.")
def format_prompt(prompt, state):
    return prompt + FORMAT_RULE
