# Dream-RSI 阅读笔记（arXiv 2609.14858v1，2026-09-14；Google / DeepMind / UMD / UVA）

核对方式：完整 PDF 共 36 页，提取文本后 grep；引文均为原文。

## 角色与模型
- **Discovery / coding agent**：Gemini-3.1 Pro 和 Gemini-3.7-Flash，通过 Gemini CLI 调用。原文："We use Gemini-3.1 Pro via the Gemini CLI as the discovery agent"。
- **Policy-development agent**（附录 B.2 里叫 controller-development agent）：原文是 "A fixed LLM-based policy-development agent uses this feedback to revise the exploration policy code"。**全文没有说明它用的是哪个模型**，也没有对它的能力强弱做消融。
- **Evaluator**：固定的、任务特定的打分程序，不是 LLM，比如运行时间、数学目标值、kernel 的 1/ms。
- 原文："Only the exploration-policy code changes; the underlying models, evaluator, and execution interfaces remain fixed."

## 被演化的是什么
- 一段**探索策略代码**，接口是 `OptimalPolicy.solve`。它决定从发现树的哪些叶子继续扩展、并行开几个尝试、何时停止，也就是**算力分配策略**，不涉及任务知识。
- prompt 里明确限制："Do not solve the scientific task"，而且只能使用 prefix-observable 的信息。

## Replay simulator（"dreaming"）
- 用历史上已经跑出来的发现树当回放世界。候选策略在树上走不同的路径时，只"揭示"树里已经记录的结果，不重新调用 coding agent，也不重新评估。
- **纯确定性回放**：没有重要性加权，没有反事实估计，也评估不了树里没有记录的分支。
- 选择规则：$\pi_{t+1}=\pi_t^{m^\star}$，$m^\star=\arg\max_m V^m$，并且 $V^{m^\star}\ge V^0$。**这个保证只在同一份历史上成立，没有留出集，也没有过拟合控制**（存在赢家诅咒）。

## "Recursive" 指的是什么
- 递归发生在**数据和世界**这一层：更好的策略收集到更好的树，更好的树又支撑下一轮策略改进，对应标题里的 "Evolving Worlds"。
- 改进者（policy-development agent）本身是固定的，不会自我修改。按 Chen et al. 2026 的标准，这属于 bounded self-refinement，只不过作用在编排层。

## 结果（节选）
- Lasso：Gemini-3.1-Pro 的 discovery 调用从 550 次降到 317 次，6 个留出数据集上的平均运行时间从 3587.1 ms 降到 2931.0 ms。
- 数学任务：不到 1000 次生成，持平或超过 baseline（SimpleTES 用了 51,200 次）。
- KernelBench：VGG16 少用 2.43× 的生成次数，LayerNorm 少用 1.79×。

## 对我们有用的三点
1. **"把历史当回放模拟器"与我们的 replay-and-branch / 局部耦合评估是同一类想法。** 它们的弱点正好是我们的统计长处：确定性回放 + 同一份历史上取 argmax，没有不确定性量化，也没有留出验证。可以借鉴的是 IPW/AIPW、置信序列、留出确认（见 RUBRICS_AS_EXPERIMENTS_v0 的 C3/P3）。
2. **限制 proposer 能改什么，可以弱化蒸馏质疑。** 它们只允许改不含任务知识的分配策略，并且禁止解题。我们可以类似地划分：哪些编辑是"策略/分配/控制流"（不太会携带老师的知识），哪些是"任务知识"（容易被质疑为蒸馏），分开报告。
3. **§5.1 消融（已核实）**：把历史抽象成高层的"方向性建议"注入 prompt，在两种范式下都 *consistently underperforms its unguided counterpart*。这和我们 rubric round 2 的失败一致（泛化的文字诊断没用），也支持"rubric 必须可执行、可测量，不能只是文字建议"。
