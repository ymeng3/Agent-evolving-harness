# P06 family-specific few-shot exemplar (ReAct, Yao et al. 2022: 2 fixed exemplars per ALFWorld task type; the
# original ReAct ALFWorld prompt set). Static text, no learning on eval tasks -> eligible. Hook: format_prompt.
import re
EX = {
 "look_at": "Example (examine X under lamp): go to desk 1 -> take alarmclock 1 from desk 1 -> (lamp is on desk 1) use desklamp 1. If no lamp there: go to the receptacle that has a desklamp/floorlamp, then use it.",
 "pick_two": "Example (put two X in Y): find X#1 -> take it -> go to Y -> put it in/on Y -> find X#2 (check other receptacles) -> take -> go to Y -> put.",
 "clean": "Example (clean X, put in Y): find X -> take X -> go to sinkbasin 1 -> clean X with sinkbasin 1 -> go to Y -> put X in/on Y.",
 "heat": "Example (hot X in Y): find X -> take X -> go to microwave 1 -> heat X with microwave 1 -> go to Y -> put X in/on Y.",
 "cool": "Example (cool X in Y): find X -> take X -> go to fridge 1 -> cool X with fridge 1 -> go to Y -> put X in/on Y.",
 "pick": "Example (put X in Y): go to likely receptacles for X (open if closed) -> take X from R -> go to Y -> put X in/on Y.",
}
_family = lambda t: "look_at" if ("look at" in t.lower() or "examine" in t.lower()) else "pick_two" if "two" in t.lower() else "clean" if "clean" in t.lower() else "heat" if ("hot" in t.lower() or "heat" in t.lower()) else "cool" if ("cool" in t.lower() or "cold" in t.lower()) else "pick"
def format_prompt(prompt, state):
    m = re.search(r"Your task is to: (.*?)\n", prompt); fam = _family(m.group(1) if m else "")
    state["family"] = fam
    return prompt.replace("Now it's your turn to take an action.", "STRATEGY " + EX[fam] + "\nNow it's your turn to take an action.")
