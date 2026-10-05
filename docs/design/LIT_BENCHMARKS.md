# Benchmarks for BIT beyond AppWorld (survey 2026-10-04)

[verified] = arXiv abstract/HTML page or official model card opened. [snippet] = search result only. Everything else is from prior knowledge or is an estimate (est.).

## 1. What the closest 2025-26 works use

| Paper | Benchmarks |
|---|---|
| Self-Harness 2606.09498 [verified] | TB-2.0 (64), SWE-V (100: 67/33), AppWorld (180: 90/90). Qwen3.5-35B-A3B goes 18.0->36.7, 19.5->41.5, 22.5->52.2 |
| HarnessFix 2606.06324 [verified] | GAIA (150), SWE-V (250), AppWorld (225), TB-2.0-Verified (85), split about 40/20/40. GPT-5-mini |
| Meta-Harness 2603.28052 [verified] | TB-2, text classification, IMO-level math RAG |
| AHE 2604.25850 [verified] | TB-2, SWE-V |
| HarnessCompass 2608.01918 [verified] | SWE-V |
| AutoSaddler 2608.23041 [verified] | **Gaia2**, **SWE-bench Pro**, TB-2.0 |
| Mixture of Self-Improving Branches 2609.37834 [verified] | TB-2.0, SWE-Lite, Olympiad math |
| MILO 2609.38349 [verified] | TB-2.1, PaperBench, DeepSWE, EinsteinArena (gpt-oss-120b) |
| Rethinking Harness Evolution 2607.12227 [verified] | TB-2.1, ARC-AGI-3, EdgeBench (finds evolution does not beat matched-budget TTS on TB) |
| HarnessEvolve 2609.00829 [verified] | SearchQA, OfficeQA, SpreadsheetBench (Qwen3.6-27B) |
| AgentStream 2608.00155 [verified] | AppWorld, BFCL, BrowseComp-Plus, HLE, SWE-V, tau2 (50 each) |
| ACE 2510.04618 [verified] | AppWorld (incl. test-challenge), finance (FiNER/Formula) |
| AgentEvolver 2511.10395 [snippet] | AppWorld, BFCL-v3 |
| DGM 2505.22954 [verified] | SWE-bench, Polyglot |
| GEPA 2507.19457 [verified] | HotpotQA, IFBench, HoVer, PUPA |
| Dream-RSI 2609.14858 [verified] | Lasso path, math optimization, GPU kernels (not agentic) |

**Usage count (16 papers):** Terminal-Bench 2.x **8**. SWE-bench family **8** (Verified 6, Pro 1, Lite 1; DeepSWE 1 more). AppWorld **5**. GAIA/Gaia2 **2**. BFCL **2**. tau2 **1** (plus divergence-point DPO 2606.23112 [verified], tau2 with 375 tasks). BrowseComp-Plus **1**. SpreadsheetBench/OfficeQA **1**. WebArena, OSWorld, MCP-*, Toolathlon, TheAgentCompany, Spider2, DABstep, ALFWorld: **0**. For harness papers, reviewers will expect **TB-2.x plus one SWE-bench variant**.

## 2. Comparison (Q = Qwen-27B-class scores; vendor-harness numbers come from the model cards [verified])

| Benchmark | Tasks | Feedback | Exact replay of prefix | Compute | ~27B score | Fit |
|---|---|---|---|---|---|---|
| AppWorld test-challenge | 750 total (417 challenge) [verified] | per-test state checks | yes (DB snapshot) | CPU | ours 0.83 val | saturated |
| **Gaia2 (ARE)** 2602.11964 [verified] | 800 public "validation" (5 caps x 160 + A2A/noise aug); hidden test | **per write-action** oracle verifier; soft args judged by an LLM (Llama-3.3-70B default) [verified] | **yes**: deterministic sim, seeds, time pausable / "instant" mode [verified] | CPU + judge LLM | Kimi-K2 20%, GPT-5 42% (2025) [verified]; Q8-27B est. 30-45% | **best** |
| **SWE-bench Pro** 2509.16941 [verified] | 731 public (+Pro-Verified 2609.08149 [verified]) | FAIL/PASS test lists + logs | mostly: replay edits/commands in a fresh image; test flakiness | docker, about 730 large images | Q3.6-27B 53.5, Q3.8-27B 61.7 (vendor) [verified]; simple harness est. 30-45 | **high** |
| Terminal-Bench 2.0/2.1 2601.11868 [verified] | 89 (2.1 patches 28) [verified] | pytest per task | partial: network, clock, background processes | docker | Q3.8-27B 73.0 (TB2.1), Q3.6 59.3 [verified]; Self-Harness Qwen3.5-35B 18% | too few tasks; expected |
| SWE-bench Verified / SWE-Gym | 500 / 2,438 [verified] | test-level | as Pro | docker | Q3.6-27B 77.2 [verified] | saturated; Gym is a train pool |
| DeepSWE 2607.07946 [verified] | 113 | functional verifiers | as Pro | docker (Harbor) | Q3.8-27B 42.2 [verified] | small |
| tau2/tau3-bench | about 280 (+banking) | DB-hash + expected actions | env yes; **user simulator is an LLM** (log its turns for the prefix; branches are stochastic) | CPU + user-sim LLM (standard is GPT-4.1) | Q3.5-27B 79.0 [verified] | saturated, LLM-in-loop |
| BFCL v3/v4 multi-turn | 1,000 MT (200 x 5) [verified] | per-turn state + response checks | yes (Python API classes) | CPU | Q3.5-27B 68.5 overall [verified] | easy to run, short horizons |
| Gaia (v1) | 165 val / 300 test | answer only | no (live web) | browser | — | no |
| BrowseComp-Plus 2508.06600 [verified] | 830, fixed 100K-doc corpus | answer only (LLM judge) | yes (static corpus) | GPU retriever | Q3.5-27B BrowseComp 61 [verified] | coarse feedback |
| WebArena-Verified | 812 / hard 258 [snippet] | deterministic evaluators | costly: container reset per task; DOM nondeterminism | 6 web dockers | Q3.8-27B 64.8 [verified] | heavy |
| OSWorld-Verified | 369 [snippet] | execution checkers | no (GUI timing) | VMs, VLM | Q3.8-27B 84.3 [verified] | saturated |
| Toolathlon 2510.25726 [verified] | 108 | eval scripts | partial (some remote SaaS) | many dockers + accounts | best open 20.1% (2025) [verified] | too few tasks, accounts needed |
| MCPMark 2509.24002 [snippet] | 127 | verify scripts | partial (Notion/GitHub are live) | accounts | GPT-5 52.6% | accounts needed |
| MCP-Universe / MCP-Bench / LiveMCPBench | — | real APIs / LLM judge [verified] | no | live APIs | — | no |
| TheAgentCompany 2412.14161 [verified] | 175 | checkpoints, some LLM-judged | no (LLM NPCs) | many dockers | best 30% (2024) | heavy |
| SpreadsheetBench 2406.14991 [verified] | 912 | OJ-style multi-test cells | yes (file + code) | CPU | DeepSeek-V4-Flash 44.3 (HarnessEvolve) | single-turn-ish |
| Spider 2.0 2411.07763 [verified] | 632 | result match | yes for SQLite | BigQuery/Snowflake (paid) | — | paid DBs |
| DABstep 2506.23719 [verified] | 450+ | answer only, hidden test | yes | CPU | — | coarse |
| OfficeBench, ALFWorld/SciWorld/WebShop, LiveCodeBench | — | — | yes | CPU | — | dated / not agentic |

## 3. Recommendation (ranked)

**1. Gaia2 / ARE (primary, AppWorld successor).** It is the closest structural match to BIT. It is a deterministic Python simulation of 10 mobile-app "universes" with about 101 tools each. Seeds plus pausable/instant time make logged-action replay exact. The verifier compares agent write-actions with oracle events, so it gives per-action failure text, a direct analogue of AppWorld's test text as privileged hindsight. 800 public scenarios allow a 300/150/350 split. Headroom is large (open SOTA about 20% in 2025), and the failure modes are ones a harness rule can target: acting on ambiguous tasks without asking, missing time-triggered events, giving up on search. Cited by AutoSaddler. **Main risk:** the soft-check LLM judge (default Llama-3.3-70B) is not available locally at the same size. Use a pinned local judge (Qwen3.8-27B at temperature 0), cache verdicts, and report agreement on a subset. Exact replay also has to restore the **simulated clock and the event queue**, not just the actions. Exclude Agent2Agent (LLM sub-agents) and check that Noise is seeded.

**2. SWE-bench Pro (public 731; report the Pro-Verified subset).** This is the expected coding venue (SWE family: 8/16 papers) and is not saturated for 27B with our own harness. FAIL_TO_PASS/PASS_TO_PASS give test-level hindsight, and file edits replay deterministically. Use SWE-Gym or the Pro train repos for proposer training if needed. **Main risks:** (a) replay fidelity. Commands with side effects (pip, background servers, randomness in tests) can diverge. Mitigate by replaying only file-system and command actions, `docker commit` at the branch point, and checking prefix fidelity by hashing the repo tree. (b) Throughput and disk. About 730 images (tens of GB each in some cases) and long thinking trajectories on one A800 mean you need to subsample (e.g. 300 tasks, 120/60/120).

**3. Terminal-Bench 2.1 (held-out transfer, not a training benchmark).** 8/16 related papers report it, so reviewers will ask. Its 89 tasks are too few for train/val/test, so use it to check that harness trees learned on Gaia2/SWE transfer, or follow HarnessFix's 34/17/34. Note that 2607.12227 shows harness evolution fails to beat matched-budget test-time scaling there, so include a TTS baseline. **Main risks:** replay is not exact (internet access, timing, process state), so branch from `docker commit` snapshots instead of re-executing. Headroom is also limited (Q3.8-27B scores 73 with Terminus).

Not recommended now: tau2/tau3 (saturated at 79 for Q3.5-27B, and the LLM user simulator makes branches stochastic), BFCL (deterministic but short-horizon; a cheap sanity domain at most), and WebArena/OSWorld (heavy, and saturated for Qwen3.8-27B).
