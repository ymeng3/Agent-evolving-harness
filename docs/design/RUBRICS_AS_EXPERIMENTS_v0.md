# Rubrics as Experiments — 设计草案 v0（2026-10-01）

> 来源：13-agent 设计流程（3 个文献 scout + 1 个服务器实证检验 + 4 个独立框架〔效率 / 信息论 / 泛函梯度-因子 / 诊断-因果〕+ 4 份对抗审稿 + 综合），再加人工核对。
> 状态：**讨论稿，尚未冻结，不是 prereg。** 标 [verified] 的文献是 agent 在检索里确实看到的；[unverified] 需要自己查。
> 原始材料：服务器 `/root/autodl-tmp/cc/tmp/ic_check/`（实证脚本和输出）。

---

## 0. 一句话

**在 AppWorld 上，rubric 不可能是更好的"标签"，只能是更好的"实验"。** 每个 rubric 维度写成一个可执行的机制程序，形式是（触发条件, 标准修复, 安慰剂, 反证）。它的价值用"在它触发的地方做干预，真实成功率能提高多少"来衡量，而且只在编辑真正起作用的位置测量（replay-and-branch）。最终的继承决定只看真实结果，rubric 只负责"往哪里看、往哪里改"，所以即使 rubric 写错了，也不会让估计产生偏差。

候选标题：*Rubrics as Experiments: Localized Counterfactual Evaluation for Self-Evolving Agent Harnesses*（备选 *Measure Where It Acts*）。

---

## 1. 关键转折：为什么不能把 rubric 当作 surrogate 或 reward label

- 在 AppWorld 上，一条轨迹跑完，`won` 和 `G` 也就有了，**真实标签是免费的**。贵的是生成轨迹，不是打标签。
- 半参数理论给出的结论很明确：所有样本都有主结果时，辅助 surrogate 不会带来任何效率提升（Kallus & Mao [verified]）。PPI、控制变量这一类方法之所以有用，前提是"主结果缺失或昂贵"，而我们这里不成立。
- 用轨迹后特征（G、步数、是否调用 `complete_task`）去做控制变量是**无效的**：这些特征是编辑施加以后才测到的，本身就被处理影响了，期望差未知。实证检验里算出的 $1-\rho^2\approx0.37$ 看起来很漂亮，但**不能用**。
- 编辑施加之前就能测到的协变量（CUPED 式），方差最多只能再降约 5%，因为配对已经把任务效应去掉了。

**结论：** "新维度是否让估计更准"这个标准在这里恒为零。维度的价值只能来自两处：**(a) 指出可以修的缺陷**，**(b) 让实验更省**。这也解释了之前 PRM judge 和泛化 rubric 为什么失败：它们都试图当更好的标签。

> 以后如果换到没有可验证奖励的开放任务，surrogate 和 PPI 的视角就重新成立，但那是另一篇论文。

---

## 2. 实证底数（服务器已有日志，只读分析，2026-09-30）

| 量 | 值 | 含义 |
|---|---|---|
| won 的任务间方差占比 | 0.646（seed 间一致率 82%，κ=0.64） | 任务难度是主导的"市场因子" |
| G 的任务间方差占比 | 0.462 | **G 的可复现性不如 won**，稠密不等于稳定 |
| 配对 vs 独立的标准误（won） | 0.101 → 0.060（方差比 0.354，有效样本 ×2.8） | 按任务配对有效 |
| 50 题配对的最小可检测效应（80% 功效） | won 16–17pp；5pp 需要约 11 次完整评测 | 靠整次评测给每个维度逐一验证，**不可行** |
| 同 patch、同 seed 重复跑 | G 分别为 0.9 / 0.7 / 0.7 | 固定 seed 复现不了轨迹，配对只去掉了任务效应 |
| 植入效应（30 步 vs 25 步，约 +16pp）的功效 @ n=50 | won 0.77，G 均值 0.71，**G 符号检验 0.89** | 秩/符号统计有效，原因是 G 的噪声是全有或全无的跳变，不是因为 G 稠密 |
| 截断评测能否当廉价代理 | 第 10 步时 G 在所有题上都是 0；第 25 步时 AUROC 0.84–0.92 | goal check 都在后期才通过，没有早期代理 |
| 失败构成 | **75–88% 的失败在 30 步内从未调用 `complete_task`**；调用了的题 P(won)=0.81–0.90 | **瓶颈是步数预算和效率，不是答案格式** |
| 胜利出现的时间 | 中位数第 21–24 步，约 40% 的胜利在第 25 步以后 | 预算 H=30 是紧约束 |
| 解析修复后的 F0（discovery） | 26/50（原 18–19/50），但**仍有 11/50 题出现 default-code 步**，这些题胜率只有 27% | 两个修复（解析 + 超时）的效果混在一起；default-code 混杂只减少了，没有消除 |
| 现有的 50 题配对 | 只有 1 对（验证集 strip-answer），两者只在 2/50 题上有差别 | 发散率 s=0.04，这一对**永远分不开** |

---

## 3. 形式化框架

**对象。**
- harness $h$，步数预算 $H=30$。
- 轨迹 $\tau=(\sigma_0,a_0,\sigma_1,\dots)$，其中 $\sigma_k$ 是前缀（历史、环境状态、hook 状态）。
- 结果：$Y=$ `won` 是主结果；$G$ 和完成步 $K$ 是次要结果。
- $Q^h(\sigma)=\mathbb E_h[Y\mid\sigma]$，$J(h)=\sum_t\omega_t\,\mathbb E_h[Y\mid t]$。

**发散时刻。** 编辑 $e$ 的 $\kappa_e(\tau)$ 定义为：在已记录的前缀上以影子模式运行 $e$ 的 hooks，第一次会改变消息、解码参数或所执行代码的那一步。
- 发散率 $s_e=P_h(\kappa_e<H)$。
- 分支成本 $f_e=\mathbb E[(H-\kappa_e)/H\mid\kappa_e<H]$。
- 每步都起作用的编辑有 $\kappa_e\approx0$，也就是 $s\approx1$。

**Rubric 维度** $j=(T_j,F_j,\tilde F_j,C_j)$：
- 前缀谓词 $T_j$（触发 ∧ 证据），在 $\kappa_j$ 处触发；
- 标准修复 $F_j$，要求非 oracle，只能用前缀信息生成的提示或控制流动作；
- token 数匹配的安慰剂 $\tilde F_j$；
- 反证谓词 $C_j$，满足时 $F_j$ 必须保持沉默。

这就是 Phase-2 的 `FailureMechanism` schema 变成了可执行形式。

**Headroom（可修复缺陷，也就是"梯度"）。**
$$\eta_j=J(h\oplus F_j)-J(h\oplus\tilde F_j)=s_j\,\bar a_j,\qquad \bar a_j=\mathbb E[\Delta_j(\sigma_{\kappa})\mid\text{fire}],\quad \Delta_j=Q^{h\oplus F_j}-Q^{h\oplus\tilde F_j}.$$
$\eta_j$ 是 $J$ 沿机制 $j$ 的**因果方向导数**，已经扣掉了"任何打断都有帮助"的安慰剂效应。所有维度的 $\{(s_j,\bar a_j)\}$ 合起来构成**缺陷地图**：$s_j$ 大的是一般能力问题，$s_j$ 小的是边缘情况。它由干预识别，不存在旋转不定性，也不会和任务难度混杂。

**低秩层（接你的 AoS 框架）。**
- $\Theta\in\mathbb R^{T\times J\times A}$（任务 × 触发类型 × 干预 $a\in\{\emptyset,F_j,\tilde F_j,e_1,\dots\}$），$\theta_{tja}$ 是在 $j$ 第一次触发时施加 $a$ 后成功率的 logit。
- 一次分支观测：$X=e_t\otimes e_j\otimes e_a$，按已知设计 $p(x)$ 放在触发位点。设计只依赖前缀，不依赖结果。$Y\sim\text{Bern}(\sigma(\langle\Theta,X\rangle))$，来自一个新采样的后缀。
- 这正是你论文里的单指标 GLM，已知的非均匀抽样：$G(p)=\sum_xp(x)I(\eta_x)X_x\otimes X_x$，$A(p)=P_TG(p)P_T$，$H=A^{-1}P_T\Gamma$，$V(p)=\langle P_T\Gamma,H\rangle$。
- **rubric 分数只通过"设计"和"proposer"进入，不进入似然。** 各分支条件独立，信息量可以相加，不会在同一条轨迹里重复计数。
- 低秩是**有门槛的**，不是默认假设。一阶的提速来自耦合（§4-C2），低秩结构要等 held-out deviance 证明有用才启用。

---

## 4. 判据：新维度是否有效（回答"数学化量化"）

**C1 可修复缺陷（梯度）。** 在 $D_E$ 的触发位点上估计：
$$\hat\eta_j=N^{-1}\sum_i\mathbb 1\{\kappa_{ij}<H\}\tfrac{R_i}{\pi_i}(Y_i^{F}-Y_i^{\tilde F}),$$
用按任务聚类的 anytime-valid 置信序列给出 $p_j$。
- **准入**需要同时满足三条：
  1. $p_j\le\alpha_j$，并且**每一个被提出的维度**都要支付 α-investing 财富（Foster–Stine [verified]），用来控制 mFDR；
  2. 在 $C_j$ 成立的地方，$F_j$ 保持沉默；
  3. 如果和已有维度 $k$ 的触发集合重叠超过 20%，要求增量 headroom $\eta_{j\mid k}=\mathbb E[\mathbb 1\{\text{fire}\}(Q^{F_k\circ F_j}-Q^{F_k})]$ 的 LCB > 0。这就是 factor zoo 的"边际贡献检验"。
- **合并**：两个维度互为替代（彼此的增量 headroom ≈ 0）时，保留 $\Lambda$ 更大的那个。
- **退役**：当前 incumbent 上 $\text{UCB}(\eta_j)<1$pp，或者 $s_j<2\%$（奖励太平就学不到东西，Razin et al. [verified]）。每 2 轮重新检验一次，因为维度的价值依赖当前策略。
- 泛化维度按构造就有 $\Delta\approx0$，会被自动拒掉。"机制指标过关但成功率下降"会得到 $\eta<0$，被拒掉。这正对应存档里 fallback 的教训：机制通过，结果 −16.4pp。

**C2 每次评测的信息量（信息增益）。** 在首次发散处耦合（见 §6 P1）时，相对效率为
$$\mathrm{RE}_j=\frac{v_{\text{pair}}}{s_j^2\,f_j\,v_j},$$
其中 $v_{\text{pair}}\approx0.18$ 是整次评测配对对比的每题方差，$v_j$ 是每个位点上分支对比的方差（**尚未测量**）。
- 没有发散的轨迹贡献**恰好为零**。这是一个恒等式，不是假设。
- 所以边缘情况（$s$ 小）用耦合反而**更容易测**：达到同样精度所需的评测次数和 $s$ 无关，而配对整次评测需要的次数按 $1/s^2$ 增长。
- 写成 AoS 形式：维度 $j$ 加入的 Schur 补信息为 $B_{j\mid N}$，对决策泛函 $\psi$ 的价值是
$$\Delta V_j/c_j=\big[\langle h,A^{-1}h\rangle-\langle h,(A+B_{j\mid N})^{-1}h\rangle\big]/c_j,$$
其中 $\tfrac12\log(V_{\text{before}}/V_{\text{after}})$ 就是**目标化的信息增益**。它等于 0，当且仅当 $j$ 的位点和最不利方向 $H$ 正交。

**C0 价值率（用于分配，不用于判定）。**
$$\Lambda_j=\tau_j\eta_j/n_j=\tfrac{50}{z^2}\,\eta_j\,\tau_j\,\mathrm{IR}_j^2,\qquad \mathrm{IR}_j=\tau_j\bar a_j/\sqrt{f_jv_j}.$$
- $\tau_j$ 是**迁移率**：proposer 真实写出的编辑能兑现标准修复多大比例的收益。
- 这就是 Grinold 基本定律 $\mathrm{IR}=\mathrm{TC}\cdot\mathrm{IC}\cdot\sqrt{\mathrm{BR}}$ 的字面版本：$\mathrm{IC}_{\text{loc}}=\bar a/\sqrt v$，$\mathrm{TC}=\tau$，$\mathrm{BR}=1/f$。
- 选下一个攻击目标时，用 Thompson 采样按 $\Lambda$ 抽取。

**C3 Goodhart 保护。** 继承只看真实的 $\psi_e=J(h\oplus e)-J(h)$，用 AIPW 估计：
$$\hat\psi_e=N^{-1}\sum_i\mathbb 1\{\kappa_{ie}<H\}\big[\hat m_i+\tfrac{R_i}{\pi_i}(Y_i^e-Y_i^\emptyset-\hat m_i)\big].$$
这里 $\hat m$ 是交叉拟合的低秩工作模型，**不论 $\hat m$ 好坏，估计都无偏**。
有效性依赖 5 条可审计的假设：
- A1 精确 replay
- A2 发散和门控
- A3 已知且可由前缀测得的 $\pi\ge\pi_{\min}$
- A4 后缀之间条件独立
- A5 服务端平稳

**这 5 条都不涉及 rubric。** rubric 只影响 regret，不影响错误率。

---

## 5. 演化循环（伪代码）

```
冻结 h0：修掉 default-code 路径；记录完整回复；影子 replay 时重建 hook 状态；加门控 wrapper
B ← h0 在 D_E（≥150 条）和 V（≥100 条）上的基线日志；W ← α 财富
R ← 8 个种子维度（反复翻文档、重复的 API 错误、连续执行错误、无进展循环……）
for round r = 1..6:
  U ← D_P 上没有任何已准入维度在预算耗尽前 ≥8 步触发的失败      # 残差 = 泛函梯度
  J_new ← LLM(U 里同一任务的成功/失败对比) → 可执行维度 (T, F, F~, C)
  离线筛选（$0）：s_j, f_j, 与 R 的重叠, 同一任务内"触发 vs 失败"的关联 → 取前 k 个
  对 top-k ∪ R 中过期的维度：在 D_E 上序贯地跑 F_j vs F~_j 分支，直到置信序列给出结论或触及上限
      按 C1 准入 / 合并 / 退役；更新 W
  j* ~ Thompson(Λ);  E ← proposer(j*, D_P 证据) → ≤4 个门控在 T_j* 上的编辑    # best-of-n 上限（Gao et al. [verified]）
  for e in E: 影子 replay → κ_e      （死 hook：s_e=0 ⇒ ψ_e=0，不花 GPU）
      在 κ_e 处分支；π 用成本加权 Neyman / c-最优设计（P2）；由置信序列决定何时停
  e* ← top-two Thompson；在 V 上用新分支确认（α-spending）
  if 通过: h ← h ⊕ e*;  用 e* 的分支替换 B 里对应的触发后缀        # 精确样本（P1d）
  审计：A–A 空分支、replay 抽查、每轮 +1 次新的基线评测
```

非局部编辑（$\kappa\approx0$）仍然走按任务配对的整次评测。

---

## 6. 可以证明的命题（按性价比排序）

1. **P1 局部耦合与稀释定律**（约 1 周，性价比最高）。在 A1–A5 下：
   - (a) $\psi_e=\mathbb E_h[\mathbb 1\{\kappa_e<H\}(Q^{h\oplus e}-Q^h)(\sigma_{\kappa_e})]$，即停时版本的 performance-difference lemma；
   - (b) 耦合 IPW 估计无偏，方差有显式表达；
   - (c) $\mathrm{RE}=v_{\text{pair}}/(s^2fv_{\text{site}})$；
   - (d) 把分支替换进基线后仍是 $h\oplus e$ 的精确 i.i.d. 样本。
   - 推论：每步都起作用的组件 $s\approx1$，所以 $\mathrm{RE}\approx1$；触发型组件 $s$ 小，$\mathrm{RE}$ 大。**这正好解释了 ALFWorld 上 local CF 的结果**：fallback 3/3、retry 6/7 判对，history 和 temperature 失败。
2. **P3 rubric 演化下的 Goodhart-safe 接受规则**（1–2 周）。只要 rubric、编辑和 $\pi$ 相对过去的数据是可预测的，AIPW 的增量就是鞅差。于是对**任意** rubric 都有 $P(\text{继承了 }\psi_e\le0\text{ 的编辑})\le\alpha$，再加上 α-investing 得到 mFDR ≤ α。证明用 Ville 不等式。
3. **P2 维度价值 = 目标化信息；c-最优分支**（4–5 周，是你 AoS 框架的招牌定理）：
   - (i) $V(p)$ 是凸的；
   - (ii) Schur 补 $B_{j\mid N}$ 使 $\Delta V_j\ge0$，等号成立当且仅当 $B_{j\mid N}H=0$；没有秩耦合时 $\Delta V_j=0$，这是 Kallus–Mao 的 no-free-lunch 在模型内部的版本；
   - (iii) 成本约束下 c-最优设计的等价条件（Elfving / Kiefer–Wolfowitz 型），在耦合情形下退化为成本加权 Neyman 分配；
   - (iv) 可预测设计下的 one-step CLT（鞅推广）。
   - 时间不够的话，先证固定设计下的 (i)–(iii)。

---

## 7. IC vs MSE：哪些能搬过来，哪些不能

**能搬过来的：**
- **分块（blocking）**：按任务配对，就是量化里的截面去均值，方差比 0.354。
- **秩/符号统计的稳健性**：G 的噪声是全有或全无的跳变，所以 G 的符号检验功效 0.89，高于 G 均值检验的 0.71 和 won 的 0.77。
- **breadth**：$t\approx\mathrm{IC}\sqrt{N_{\text{eff}}}$。IC=0.1 时，要约 900 个有效对比才能达到 $t=3$。
- **增量 IC 作为准入规则**（AlphaGen、Barillas–Shanken [verified]）：在我们这里就是 C1 的增量 headroom。

**不能搬过来的：**
- **功效不是白来的**：Pearson IC 的 t 统计量，和同一份去均值数据上回归斜率的 t 统计量完全相等。
- **稠密不是功效的来源**：G 的均值检验功效 ≈ won。
- **同一次运行内算出的 IC 是机械相关**：`complete_task` 的 IC 高达 +0.69，是因为没调用它就不可能赢。
- **跨候选的 IC 需要很多候选**：36 个候选时，可检测的偏相关 r ≈ 0.46。
- **符号检验换了估计量**：它估计的是 $P(\Delta G>0)-P(\Delta G<0)$，不是均值差。

**为什么 MSE 看起来是平的：** 局部效应 $s\bar a$ 被 $s$ 稀释，又淹没在编辑根本不起作用的那些轨迹的噪声里。**真正管用的"IC"是在最细的扰动上分块，在信号所在的地方测量。** 耦合是在整个前缀上分块，并丢掉所有没发散的轨迹。

**实际使用的统计量：**
1. 局部编辑：耦合 AIPW 均值（won）+ 分歧分支对上的精确 McNemar 检验；
2. 非局部编辑：按任务配对的 won + sign-flip 随机化检验；G 符号检验作为事先声明的次要检验，要求它和 won 均值差同号才接受；
3. 筛选：同一任务内跨运行的"触发 vs 失败"对比，按任务做 Fama–MacBeth，任务聚类。

---

## 8. 实验与门槛（约 300 次评测；假设我们每天能用 15–20 次）

| 阶段 | 内容 | 成本 | Go/No-go |
|---|---|---|---|
| **F0**（第 1 周） | 对 24 个 Phase-2 候选和 8 个种子维度做影子 replay：发散率、κ、预测 RE；测 replay 保真度；对 `complete_task` 门控的候选做完成步 replay | **不用 GPU**（CPU replay） | 保真度：步 ≥95%，结果 ≥98%；耦合 SE ≤ 配对 SE 的 ⅓；≥3 个种子维度在 ≥20% 的"预算耗尽型失败"上触发，且触发时剩余 ≥8 步 |
| E1（第 2 周） | 冻结 h0（记录完整回复）；30 个位点 × 4 条空分支，测 $v_{\text{site}}$ 和 A–A 漂移；对 40 个预算耗尽的失败再续跑 10 步，测余量上限 | ~10 次 | A–A 的 CI 在 ±3pp 内；$v_{\text{site}}\le0.5$ |
| E2（第 3–4 周） | 用植入的门控效应（3–10pp）加 4 个真实编辑做校准。基线：配对整次评测、非配对、Loop-1 固定 n 的 LOO | ~25 次 | 实现的 RE 中位数 ≥ 预测值的一半；90% CI 覆盖率 ≥0.85 |
| E3（第 5–7 周） | 约 30 个维度的 headroom 账本：8 个种子、约 15 个残差引导、4 个泛化、3 个 token 匹配 | ~40 次 | ≥3 个维度被准入；泛化和 token 匹配维度的准入率 ≤α |
| E4（第 7–9 周） | 方向试验，3 组 × 24 个编辑：A 按 rubric 定向；B 同样门控但诊断被打乱；C 不用 rubric | ~55 次 | A > B（单侧 p<0.05）；否则只声称"局部化评估"的价值 |
| E5（第 9–12 周） | 闭环，3 组 × 6 轮，等评测预算 | ~150 次 | 次要终点（MDE ≈7pp） |
| E6（第 13 周） | 最终 incumbent 在新 V × 3 seed 和密封集 × 3 seed 上测 | ~24 次 | — |

**三张主图：**
1. 稀释定律：每个编辑或维度的预测 RE vs 实现 RE（log–log）；
2. headroom 账本：各轮每个维度可回收的失败量，从一般能力到边缘情况；
3. 各组的编辑提升分布，以及真实成功率随累计评测次数的变化。

---

## 9. 我（主会话）的判断与保留意见

1. **转折本身是对的，而且救命。** "标签免费 → surrogate 价值为零"这一条，一下子解释了 PRM judge 和 rubric round 2 为什么失败，也避免我们再在"更好的 reward model"上花三个月。
2. **最硬的贡献是 P1 稀释定律。** 它便宜（证明约 1 周，F0 不用 GPU），能解释项目的全部历史，也和你的专长完全对口。P2 是招牌定理，但要 4–5 周，而且依赖低秩结构真的存在，现在只有 2 个 patch 共享同一组 50 题，没有证据。
3. **框架偏重，有拼盘风险。** Λ、τ、Thompson、α-investing、AIPW、置信序列、低秩 Θ 同时出现，读者会累。建议论文主线只保留三件事：
   - 稀释定律 + 局部耦合评估（P1）；
   - rubric 维度 = 可执行机制，价值 = 带安慰剂的干预 headroom（C1）；
   - Goodhart-safe 保证（P3）。

   AoS 的目标化信息（P2）视时间决定放正文还是附录。
4. **最大的工程依赖是 A1 精确 replay，目前并不满足：**
   - replay 时 assistant 轮只放代码，不放原始回复；
   - 日志只保存回复的最后 600 个字符；
   - replay 分支里 v3 的 `pre_call`/`post_exec` 没有执行，hook 状态不会被重建；
   - AppWorld 状态（时间戳、ID）是否确定性，还不知道。

   **F0 的第一件事就是测这一条。不满足的话，整条线要降级。**
5. **数据指向的瓶颈是步数预算。** 75–88% 的失败是没跑完。H=30 这个选择会塑造所有结论，冻结 h0 之前应该有意识地定下 H（30 还是 40）。高 headroom 的维度很可能都是效率类：翻文档、错误连击、无进展循环。
6. **旧 baseline 被污染了。** F0 从 18–19/50 变成 26/50，混合了解析修复和超时修复。Justin 之前的所有 AppWorld 数字都可能受 60 秒超时和 default-code 的影响。
7. **死编辑已经确认**：Phase-2 的 24 个候选里，4 个只有 `post_exec`，没有任何读取方；8 个只在 `complete_task` 时起作用。影子 replay 可以零成本把这类编辑筛掉。

---

## 10. 需要决定的问题

1. 现在能改日志吗？（记录完整回复；影子 replay 时重建 hook 状态。）只改在 `cc/dev` 分支上，不影响 Justin。
2. 是否允许要求 rubric 定向的编辑**必须门控**，也就是触发之前不能有任何 setup 行为或每步行为？
3. 标准修复 $F_j$ 能否由 LLM 根据前缀生成？是否要加一个只用于报告、可以读 goal check 的 oracle 上限组？
4. 我们每天实际能用几次评测？能否和 Justin 的 job 并行跑 CPU replay？
5. 步数预算 H：30 还是 40？
6. 和 Justin 的 Phase-2 计划怎么合并？他的 rubric v3 "机制级"要求，正是这里的维度定义。
