## Proposer vs executor roles in self-evolving / automated-design systems

[V] means I read the role facts in the primary source during this session. "Stronger?" asks whether the proposer is stronger than the executor.

### A. Harness, scaffold and agent-design systems (no weight updates)

| System | Proposer / diagnoser | Executor | Same? | Stronger? | Strength ablation / same-model evidence | Claim |
|---|---|---|---|---|---|---|
| **DGM** (Zhang et al. 2025, 2505.22954) [V] | **OpenAI o1** reads the eval logs and proposes the change ("better reasoning capabilities than other FMs"). Claude 3.5 Sonnet (New) implements it | Claude 3.5 Sonnet (SWE-bench), o3-mini (Polyglot) | No | Yes | No proposer ablation; transfer to o3-mini and Claude 3.7. The diagnosis prompt includes the private test patch | "self-improving", "self-referential"; admits it is "limited by the capabilities of the underlying FM" |
| **HGM** (Wang et al. 2025, 2510.21614) [V] | GPT-5, or Qwen3-Coder-480B | GPT-5-mini, or Qwen3-Coder-30B-A3B | No | Yes | Same backbones for all baselines | self-improving coding agent |
| **Hyperagents / DGM-H** (Zhang et al. 2026, 2603.19461) [V] | Claude 4.5 Sonnet | GPT-4o (paper review), o4-mini (IMO grading), Claude 4.5 Sonnet (robotics) | Mixed | Mostly yes | none | "self-referential", metacognitive |
| **SICA** (Robeyns et al. 2025, 2504.15228) [V] | Sonnet 3.5 v2 (plus an o3-mini reasoning sub-agent) | same system | **Yes** | No | Gains "marginal" when the base model is already strong | self-improving. Says ADAS "is not self-improving, as there are two separate agents" |
| **Gödel Agent** (Yin et al. 2024, 2410.04444) [V] | gpt-4o-2024-05-13 | gpt-3.5-turbo-0125 | No | Yes | none | "recursive self-improvement" |
| **ADAS** (Hu et al. 2024, 2408.08435) [V] | GPT-4 meta agent | GPT-3.5 | No | Yes | Transfer to Claude Haiku/Sonnet and GPT-4 only | "automated design" |
| **AFlow** (Zhang et al. 2024, 2410.10762) [V] | Claude-3.5-sonnet | GPT-4o-mini, DeepSeek-V2.5, GPT-4o, Claude-3.5-sonnet | Only in the Claude row | Mostly yes | none | automated workflow generation |
| **AgentSquare** (Shang et al. 2024, 2410.06153) [V, partial] | proposer LLM πθ; model not stated separately in what I read | GPT-3.5-turbo / GPT-4o | Unclear | Unclear | none | automatic agent search |
| **W4S** (Nie et al. 2025, 2504.04785) [V, abstract] | trained 7B meta-agent | GPT-3.5-Turbo / GPT-4o | No | **No, weaker** | Weak designer still beats ADAS/AFlow by 2.9–24.6% | "weak-for-strong" |
| **Meta-Harness** (Lee, …, Khattab, Finn 2026, 2603.28052) [V] | Claude Code with Opus-4.6 | GPT-OSS-20B; Haiku 4.5; Opus 4.6 (TerminalBench-2) | Only the Opus row | Mostly yes | Opus→Opus harness ranks #2 among Opus-4.6 agents | "automated harness engineering" |
| **AI4AI strong-to-weak** (Qian et al. 2026, 2608.12307) [V, abstract] | stronger builder | weaker target | No | Yes, by design | Target score 0.49→0.91. Harness quality rises monotonically with builder reasoning effort | Explicitly "test-time **capability transfer**", presented as an alternative to OPD-style distillation |
| **Meta-Skills** (Qian et al. 2026, 2609.38143) [V] | GPT-5.6-Sol; **also** same-model Gemini-3.6-Flash / 3.1-Pro | Gemini-3.6-Flash, **Qwen3.8-Flash**, GPT-OSS-120B | Both conditions | Both | Same model in both roles: +18.71 pts on average | Calls the same-model case "self-improvement without a stronger external teacher" |
| **ACE** (Zhang et al. 2025, 2510.04618) [V] | Reflector and Curator are DeepSeek-V3.1 | Generator DeepSeek-V3.1 (AppWorld) | **Yes**, by design | No | FiNER base 70.7: weaker reflector (GPT-OSS-120B) +5.9, same model +7.6, GPT-5.1 +7.8 | "self-improving". Uses one LLM "preventing knowledge transfer from a stronger Reflector" |
| **Live-SWE-agent** (Xia et al. 2025, 2511.13646) [V] | the task LLM itself writes tools (default Claude 4.5 Sonnet) | same | **Yes** | No | GPT-5-Nano does "significantly worse" than the base scaffold | "self-evolve on the fly" |
| **STOP** (Zelikman et al., COLM 2024, 2310.02304) [V] | GPT-4 improves its own improver | GPT-4 | **Yes** | No | With GPT-3.5 and Mixtral, performance **"degrades"**; only 12% of GPT-3.5 runs gain ≥3% | "not full recursive self-improvement" because the LM is unchanged |
| **AlphaEvolve** (Novikov et al. 2025, 2506.13131) [V] | Gemini 2.0 Flash + Pro ensemble | programs plus an automatic evaluator; no LLM executor | n/a | n/a | "Small base LLM only" ablation; "performs increasingly better as the underlying LLM improves" | evolutionary coding agent |
| **ShinkaEvolve** (Lange et al. 2025, 2509.19349) [V] | gemini-2.5-pro, claude-sonnet-4, o4-mini (AIME harness task) | gpt-4.1-nano | No | Yes, by a lot | Bandit ensemble "slightly improves" over a uniform ensemble | sample-efficient evolution |
| **OpenEvolve** (codelion, GitHub README) [V] | user-configured ensemble (Gemini by default) | evaluator | n/a | config-dependent | none | open-source AlphaEvolve |
| **GEPA** (Agrawal et al. 2025, 2507.19457) [V] | reflection with the task model ("all modules … relying on the same model") | Qwen3-8B or GPT-4.1-mini | Yes, in the main experiments | No | Prompts optimized by Qwen3-8B transfer to GPT-4.1-mini (+9.00%) | reflective prompt evolution |
| **TextGrad** (Yuksekgonul et al. 2024, 2406.07496) [V] | gpt-4o as backward engine | gpt-3.5-turbo-0125 | No | Yes; explicit "weaker model … feedback generated by stronger models" | none | textual gradients |
| **MIPROv2** (Opsahl-Ong et al. 2024, 2406.11695) [V] | GPT-3.5 proposer | Llama-3-8B | No | Yes, mildly | none | LM program optimizer |
| **Voyager** (Wang et al. 2023, 2305.16291) [V] | GPT-4 writes code; GPT-3.5 for retrieval and self-QA | GPT-4 | Yes | n/a | GPT-4 gets **5.7× more unique items** than GPT-3.5 doing code generation | lifelong learning |
| **ExpeL** (Zhao et al. 2023, 2308.10144) [V] | gpt-4-0613 extracts insights | gpt-3.5-turbo-0613 | No | Yes | gpt-3.5 insights do worse (Sec. 5.6) | experiential learning |

### B. Weight-updating self-improvement (all same-model)

| System | Roles | Notes |
|---|---|---|
| **Self-Rewarding** (Yuan et al. 2024, 2401.10020) [V] | Llama 2 70B generates and judges ("assigned rewards by that same model") | — |
| **Meta-Rewarding** (Wu et al. 2024, 2407.19594) [V] | Llama-3-8B-Instruct acts as actor, judge and meta-judge | — |
| **SPIN** (Chen et al. 2024, 2401.01335) [V] | zephyr-7b-sft-full plays against itself | Still anchored to human-annotated SFT data |
| **STaR** (Zelikman et al. 2022, 2203.14465) [V] | GPT-J | — |
| **R-Zero** (Huang et al. 2025, 2508.05004) [V] | Challenger and Solver both start from the same base (Qwen3-4B/8B-Base) | Collapses "after multiple iterations"; larger models only delay it. GPT-4o is used only as an analysis oracle |
| **Absolute Zero** (Zhao et al. 2025, 2505.03335) [V] | one model proposes and solves; a code executor verifies | Gains grow with size: +5.7 / +10.2 / +13.2 at 3B / 7B / 14B |
| **SEAL** (Zweiger et al. 2025, 2506.10943) [V] | Qwen2.5-7B writes its own self-edits | After RL, 47.0% beats GPT-4.1 synthetic data (46.3%) in the single-passage setting; GPT-4.1 data is slightly better in continued pretraining |

## What happens when the proposer is weak or the same model

**Gains shrink or vanish:**
- STOP: GPT-3.5 and Mixtral degrade.
- Live-SWE-agent: GPT-5-Nano does worse than the base scaffold.
- Voyager: GPT-3.5 doing the coding gets 5.7× fewer unique items.
- ExpeL: gpt-3.5 insights are worse.
- SICA: gains are marginal on a strong base.
- AlphaEvolve: performance tracks LLM strength.
- R-Zero: self-play collapses over iterations.
- Theory (Song et al. 2024, "Mind the Gap", 2412.02674) [V]: the generation-verification gap scales with pretraining flops. With different models for generation and verification, the gap "increases with verifier capability and decreases with generator capability". Models do not self-improve on tasks beyond their inherent capability.

**Gains survive:**
- ACE: same model +7.6 versus +7.8 with GPT-5.1, so only a 0.2-point premium for the stronger reflector.
- Meta-Skills: same model +18.71.
- SEAL: self-edits ≈ GPT-4.1 data.
- W4S: a weak 7B designer still helps strong executors.
- GEPA: self-reflection works at 8B.

## Is there a consensus?

There is no formal one, but the literature uses three working tiers:

1. **Broad usage (surveys).** Gao et al. 2025 (2507.21046) [V] define self-evolution by the **"locus of autonomy"**: no human curating data or scheduling updates. It does not require the proposer to be the same model, so ADAS and AFlow are included. Under this definition, a strong external proposer still counts as "self-evolving".
2. **Strict usage.**
   - SICA rejects ADAS as "not self-improving" because it uses two separate agents.
   - STOP calls its own result "not full recursive self-improvement".
   - ACE deliberately uses one model so that knowledge does not leak in from a stronger reflector.
   - Qian et al. 2026 (2609.38143) reserve "self-improvement" for the case with no "stronger external teacher".
3. **Strong-to-weak is a recognised separate category.** Qian et al. 2026 (2608.12307) name strong-builder → weak-target harness construction "test-time capability transfer" and present it explicitly as the test-time counterpart of OPD-style distillation.

Precedents like DGM (o1 diagnoser) and HGM (GPT-5 → GPT-5-mini) still published under the "self-improving" label. Reviewers increasingly treat a stronger proposer as a confound that needs ablating.

**Your intuition is largely right.** Opus 5.5 patching a Qwen3.8-27B harness is not OPD in the strict sense, because no weights change. Structurally it is the same thing, though: a teacher critiques the student's own rollouts. The 2026 literature calls it strong-to-weak capability transfer, not self-evolution in the strict sense.

## Implications for your project

1. **Make the main condition self-proposal:** Qwen3.8-27B diagnoses and patches its own harness. Run Opus 5.5 (stronger) and gpt-4o (weaker) as ablations, and report the premium from a stronger proposer, as ACE's Table 16 does.
2. **Your existing gpt-4o results are a weak-proposer setting** (W4S-like) if gpt-4o really is weaker than Qwen3.8-27B. That framing works in your favour for the claim.
3. **Keep the diagnoser's information fixed across conditions.** DGM's diagnoser saw the private test patches, so it had privileged information. Leaked information is a second confound alongside proposer strength.

The Qwen3.8-27B specs come from your brief; I did not check them.