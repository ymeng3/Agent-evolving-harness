# Depth-wise intervention trees: policy-space boosting, v4 rounds (2026-10-06)

**Framing.** Each round adds one intervention tree $f_t$ to the harness: $h_t = h_{t-1} \oplus \eta f_t$. This is functional-gradient ascent on $J(h)=E[Y\mid h]$ in policy space. The performance-difference / CPI insight is $J(h_\eta)-J(h) = \eta\,E_{d^h}[A_f] + O(\eta^2)$, and with first-fire semantics $dJ/d\eta = s\cdot\bar a$. So a tree is worth what its leaves' local advantages add up to, weighted by how often they fire.

Up to round R2 every tree was a stump: one detector and one intervention leaf. From R3 on, trees grow depth-wise, as XGBoost does.

## Node, sample, gradient
- **Node.** A node is a set of states $S$, each a logged prefix state from the base discovery logs. The root of a round's tree is the set of firing states of the level-1 split.
- **Per-state gradient.** For an intervention leaf $\pi$ at state $s$, we have branch-at-fire continuations with and without $\pi$. The per-state causal difference is $d_s = \bar y_s^{\pi} - \bar y_s^{\varnothing}$, an unbiased estimate of the local advantage $A_\pi(s)$. These are the "per-sample gradients" inside the node; in XGBoost terms $g_s = -d_s$ and $h_s = 1$.
- **Leaf value.** The leaf value of a child $C \subseteq S$ is $\bar a_C = \mathrm{mean}_{s\in C} d_s$, the Newton step with $h = 1$. It is pooled across states with the rank-1 posterior from bit_lowrank (shrinkage $\lambda$ = prior).
- **Split gain** (squared-error / Newton form, unit hessians):
  $$\mathrm{Gain} = \frac{(\sum_{L} d)^2}{|L|+\lambda} + \frac{(\sum_{R} d)^2}{|R|+\lambda} - \frac{(\sum_{S} d)^2}{|S|+\lambda} - \gamma.$$
  Each child then gets its own leaf: the intervention if its posterior $P(\bar a_C > 0) \ge 0.9$, else "no intervention" (value 0). In policy terms this is *targeting*. Dropping the harmful sub-population raises $J$ by $-\sum_{s \in C_{\rm drop}} d_s$, which is the §5 targeting value in MATH v1.

## Who proposes the split: the hindsight self-proposer (same Qwen)
The model is given the node's contrast, which is privileged information it cannot get online:
- **Helped states** ($d_s > 0$): the prefix, the pending cell, and a continuation with $\pi$ that won.
- **Harmed or neutral states** ($d_s \le 0$, e.g. logged-won states where blocking broke the run): the prefix, and the continuation with $\pi$ that lost.
- The parent's detector, its note, and the task texts.

It proposes child detectors $\phi_c$ over the same `view`. The child intervention leaf is compiled as **parent AND child**; the complement is "no intervention". The proposer may also refine the note text of the kept leaf.

## Evaluation (no new runs needed for the first estimate)
1. **In-node partition.** Simulate $\phi_c$ on the node's states. These are the same prefix views the branch used, so we get $L/R$, the in-node Gain, and the child leaf posteriors from the **existing** branch data.
2. **Out-of-node generalisation.** Do active sampling on new states. Simulate parent AND child over all base logs, plus the extra active-sampling seeds on tasks where the parent fires. Then run branch-at-fire only on states not used to propose, with reps chosen by the candidate-level active rule. Pool the results with the rank-1 model.
3. **Admission.** The refined tree replaces the stump if both hold:
   - Gain $> \gamma$ on in-node data;
   - $P(\bar a_{\text{kept leaf}} > 0) \ge 0.9$ on held-out states, with $\ge 4$ states.

   Otherwise the stump stays. Depth is capped at 3, and a node is split only if it has at least 4 states (min_child_weight).

## Round structure (R3+)
1. Level 1: the residual-driven proposer on the base logs (as before), then screen and branch. Choose the best stump by pooled $s\cdot\bar a$ among admissible candidates.
2. Level 2..3: for the chosen stump's node (and recursively), if the node contains harmed states or $\bar a$ varies a lot across states, propose child splits, then evaluate and admit as above.
3. Merge the finished tree into the harness and re-run the base discovery logs. Residuals are recomputed for the next round.

**Retro-application to existing trees.** Tree 1 (P2_c13_1, block answer on action task) has a known harmed sub-population: question tasks without classic cues (7d26579 on disc). Its R0 branch build on H1 disc already contains per-state $d_s$; its harmed states are the logged-won ones (won-split −0.17). The first test of depth-wise growth is to refine tree 1 into "parent AND not-a-question", using that data plus active sampling of new states.

## Interpretation for the paper
This is boosting in policy space:
- the weak learner is a treatment-assignment tree whose splits come from an LLM oracle over program space;
- the leaves are causal advantages estimated by counterfactual branching;
- targeting (where not to intervene) is learned inside the tree from per-state causal differences;
- data collection is active, and estimation is pooled (low-rank).

We use the lemmas for their algorithmic insight: the weak learner maximises $\sum d^h A$, and the step size is chosen pessimistically. We do not adopt their exact constants.
