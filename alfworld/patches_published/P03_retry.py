# P03 retry on inadmissible action with explicit corrective instruction (harness-level 'retry'/re-prompt; distinct from
# Reflexion's cross-trial retry). In-episode only. Hook: retry_policy (+ choose_fallback).
import random
def retry_policy(attempt, response, action, admissible, state):
    state["n_retry"] = state.get("n_retry", 0) + 1
    return {"extra_instruction": (f"Your previous answer '{action[:60]}' is NOT an admissible action. "
                                  "Reply with <think>brief</think><action>X</action> where X is copied exactly from the admissible list."),
            "temperature": 0.0 if attempt == 1 else 0.7}
def choose_fallback(admissible, state):
    gos = [a for a in admissible if a.startswith("go to")]
    return random.choice(gos) if gos else "look"
