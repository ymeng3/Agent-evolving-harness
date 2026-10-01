# Distillation confound in "self-evolving" harness claims (as of 2026-10-01)

**Bottom line:** If Opus 5.5 writes or diagnoses harness patches for a Qwen3.8-27B executor, the result is not OPD in the technical sense. It is a teacher-guided, cross-model optimization whose proposals are filtered by the environment. Under the strict reading the literature increasingly uses, that does not count as "self-evolving" unless you add controls. The flip side matters for you: the historical setup, with gpt-4o (an arguably weaker coder) proposing for Qwen, is the more defensible "self" claim, as long as you show that gpt-4o really is weaker on the relevant skill.

## 1. What OPD is, and how a strong proposer relates to it

- **GKD.** Agarwal et al., ICLR 2024 (arXiv 2306.13649) train the student "on its self-generated output sequences by leveraging feedback from the teacher on such sequences". This fixes the train/inference distribution mismatch of off-policy KD. [verified]
- **Thinking Machines blog.** Kevin Lu et al., Oct 2025 (thinkingmachines.ai/blog/on-policy-distillation): "sample trajectories from the *student* model and use a high-performing teacher to grade each token". The loss is per-token reverse KL computed from the teacher's logprobs (`compute_logprobs`). Off-policy distillation is SFT on outputs from an external source. [verified]
- **Qwen3 report.** arXiv 2505.09388 runs "Strong-to-Weak Distillation" for the 0.6B–14B models and 30B-A3B: off-policy distillation first, then on-policy distillation of teacher logits. It reports this often beats RL at about 1/10 of the GPU hours. [verified]
- **Scope of the OPD survey.** arXiv 2604.00626 says a method is on-policy "if the training data for the student is sampled from the student's own current policy". It **excludes inference-time methods that leave model weights unchanged**. It does cover black-box teachers that give verbal feedback, e.g. Lion (Jiang et al. 2023). [verified]

**Where an Opus 5.5 proposer fits.** Your setup has the "on-policy" half of OPD: the teacher sees Qwen's own failure trajectories. It lacks the other half: no per-token teacher distribution, no weight update, and the thing being transferred is a program. Kamoi et al. (TACL 2024, arXiv 2406.01297) have a name for this: **cross-model correction**, meaning "feedback or refines the responses using models different from the model that generates initial responses". They call it "unsuitable for evaluating whether LLMs can improve their own initial responses". [verified]

It also matches TextGrad (Yuksekgonul et al., Nature 2025), where GPT-4o's feedback optimizes a prompt for gpt-3.5-turbo. [verified]

The best description is a hybrid. The teacher supplies the proposal distribution (knowledge transfer, close to DAgger [unverified]). The environment does the selection (the evidence the system generates itself). Reviewers will ask how much of each you have.

## 2. Work that names or controls for the confound

- **Self-Challenging Agents.** Zhou et al. 2025 (arXiv 2506.01716) explicitly split two settings. "Distillation": a Llama-3.1-70B challenger with an 8B executor, trained by SFT on 70B trajectories, reaching 32.2% average Pass@1. "Self-improvement": "both πexec and πtask are the same LLM" (8B with 8B), reaching 23.5%, from a 12.0% zero-shot baseline. [verified]
- **ACE (AppWorld, your benchmark).** Zhang et al. 2025 (arXiv 2510.04618) use DeepSeek-V3.1 for the Generator, Reflector and Curator, "preventing knowledge transfer from a stronger Reflector or Curator to a weaker Generator". They report +17.1% average with execution feedback only and no ground-truth labels. [verified] **This is the closest precedent and the one reviewers will cite against you.**
- **Weng, "Harness Engineering for Self-Improvement"** (Lil'Log, 2026-07-04). [verified]
  - On SIA (Hebbar et al., arXiv 2605.27276): "the task-specific agent is much weaker than the models used for the Meta-Agent and Feedback-Agent (gpt-oss-120b vs Claude Sonnet 4.6)… evidence provisional."
  - On Autodata (Kulikov et al., arXiv 2606.25996): when the strong model cannot itself be improved, "it is more like indirect distillation… with less RSI flavor."
- **El, Yuksekgonul, Zou 2025** (arXiv 2510.06711). The meta-agent is GPT-4o and the designed agents run on GPT-3.5. The design cost only breaks even at about 15k examples on DROP/MMLU, and never on the other datasets. [verified]
- **Huang et al., ICLR 2024** (arXiv 2310.01798): without external feedback, self-correction gains vanish or reverse. [verified] Kamoi et al.'s checklist: no oracle information, and "compare with strong baselines using comparable computational cost". [verified]
- **Burns et al. 2023** (arXiv 2312.09390): strong models fine-tuned on a weak supervisor's labels outperform that supervisor. [verified] The "performance gap recovered" metric is [unverified].
- **OPRO.** Yang et al. 2023 (arXiv 2309.03409) run an optimizer × scorer grid. text-bison and gpt-3.5-turbo as optimizers "get stuck at local optima with up to 20× worse optimality gaps" compared with gpt-4. [verified] "Revisiting OPRO: The Limitations of Small-Scale LLMs as Optimizers" (ACL Findings 2024): title [verified], findings [unverified].

## 3. Who plays which role in the canonical "self-improving" papers

| Paper | Proposer / modifier | Executor | Strong→weak? |
|---|---|---|---|
| ADAS (ICLR 2025, 2408.08435) | GPT-4 meta-agent | GPT-3.5 ("to reduce compute cost") | Yes. No weaker-meta-agent ablation [verified] |
| DGM (ICLR 2026, 2505.22954) | Claude 3.5 Sonnet | Claude 3.5 Sonnet (SWE-bench); o3-mini (Polyglot) | Same model on SWE-bench [verified] |
| HGM (2510.21614) | GPT-5 (expansion) | GPT-5-mini (evaluation) | Yes [verified] |
| Meta-Harness (2603.28052) | Claude Code with Opus 4.6 | GPT-OSS-120B/20B; Opus 4.6 and Haiku 4.5 on TB2 | Mostly. Concedes it works "with one particularly strong coding-agent proposer". No weak-proposer or one-shot baseline [verified] |
| AlphaEvolve (2506.13131) | Gemini 2.0 Flash + Pro | n/a (the artifact is an algorithm) | Ablations include "no evolution" and "small base LLM only" [verified] |
| SICA (2504.15228) | The same agent edits its own code | Same | Same model [verified] |

Two self-assessments are worth quoting:
- STOP (Zelikman et al., arXiv 2310.02304): "Since the language models themselves are not altered, this is not full recursive self-improvement." [verified]
- DGM: the system is "inherently limited by the capabilities of the underlying FM". [verified]

DGM's main "self" evidence is its **DGM w/o self-improve** ablation, where the meta-agent stays fixed as the base agent. Its gains "taper off quickly". [verified]

**OpenReview reviews.** OpenReview returned a bot challenge, so I could not read reviews for ADAS (D01WR1yVW2) or DGM (pUpzQZTvGY). Any claim about what reviewers said there is [unverified]. The only critique I could read is a blog: Wegner (Medium/Substack) calls DGM's label "a stretch", because the bottleneck is the frozen FM. [verified, secondary source]

## 4. Arguments that external-optimizer evolution is still legitimately "self-evolving"

- **The system is what improves.** Furong Huang's blog: "A model need not become intrinsically stronger for the agent built around it to become more effective… I would not dismiss this as 'only improving the harness.'" [verified]
- **Definitions that cover scaffold edits.** The Ren, …, Schmidhuber survey (arXiv 2607.13104) defines self-improvement as "a self-induced update operator" acting on weights *or* scaffold components (prompts, memory, tools, control logic). [verified] The operative word is "self-induced": an external Opus proposer weakens that claim.
- **The environment does the learning.** Fitness comes only from the executor's own rollouts, and the archive compounds over time (DGM). The proposer is frozen and never sees answers. Harness gains transfer across executor families:
  - AHE (arXiv 2604.25850): +5.1 to +10.1 pp cross-family, with the gain localized to tools, middleware and memory rather than the prompt. [verified]
  - ADAS: its agents transfer to Claude-Sonnet and GPT-4. [verified]

  Transfer implies the harness encodes structure, not memorized teacher answers.
- **Weak-to-strong framing.** A proposer that is weaker on the executor's skill and still improves the executor cannot be explained as distillation, by analogy with Burns et al.

**Consensus, as far as I can tell:** there is no formal agreement. The norm emerging in 2025–26 (Self-Challenging, ACE, Kamoi, Weng) is to reserve "self-improvement/self-evolving" for **same-model or not-stronger proposers**. With a stronger proposer, the expected label is "teacher-assisted / cross-model / meta-agent" optimization, and reviewers want the confound quantified.

## 5. Controls reviewers will expect in 2026

1. **Proposer grid** with the executor fixed at Qwen3.8-27B. Proposer ∈ {Qwen3.8-27B itself (the headline "self" row), gpt-4o, Opus 5.5}. Report each proposer's own AppWorld score as an executor, so "weaker" or "stronger" is measured rather than assumed.
2. **Opus one-shot harness.** Same failure-trajectory budget, a single round, no loop or archive. This tests whether iteration matters; Meta-Harness lacks it.
3. **Opus prior-only harness.** Opus writes the harness from the task description and API docs, with no trajectories. This separates teacher knowledge from on-policy diagnosis.
4. **Real distillation baseline at matched teacher tokens.** Use Opus trajectories as in-context demos, or SFT/OPD of Qwen on them, with the same Opus token budget. This answers "is it just OPD?" directly.
5. **Ceilings.** Opus as the executor in the base harness and in the evolved harness. Report the fraction of the Qwen→Opus gap that is closed.
6. **Compute- and cost-matched baselines.** Best-of-N or self-consistency at equal executor rollouts, plus dollars and tokens per proposer (Kamoi; El et al.).
7. **Leakage audit.** The proposer sees only training-split execution feedback, never ground-truth answers. Keep test-normal and test-challenge held out, keep the evaluator and LLM config read-only (as AHE does), and grep patches for task-specific hardcoding.
8. **Compounding and transfer.** Run a "w/o self-improve" ablation (fixed proposer prompt and no archive, as in DGM). Freeze the evolved harness and transfer it to other executors (e.g. a smaller Qwen, gpt-oss) and to held-out splits.
9. **Wording.** If only the Opus rows win, title the work "teacher-guided harness evolution" rather than "self-evolving".

One-line answer in Chinese for the user: 用 Opus 5.5 当 proposer 不是严格意义上的 OPD（没有改权重，也没有逐 token 的教师信号），但属于"跨模型/教师引导"的优化。按 2025–26 的主流用法，"self-evolving"要求 proposer 是同一模型或不比 executor 强；用 Opus 也可以，但要用上面的对照实验把它的贡献量化出来。