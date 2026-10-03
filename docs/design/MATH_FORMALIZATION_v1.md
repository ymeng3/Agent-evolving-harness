# 诊断 → rubric → 触发干预 的数学化（v1，2026-10-03）

目标：把我们现在做的"强模型诊断错误 → 写在线检测器（rubric 维度）→ 检测到就注入提示 → 环境检验 → 再诊断"这个闭环，写成一个统计决策问题。要求是自然、可估计、可证明，并且能解释到目前为止的实验现象：第一阶段为什么失败，诊断设计的检测器为什么能迁移，V2 为什么有效。

---

## 1. 对象

| 记号 | 含义 |
|---|---|
| 任务 $t\sim\mathcal T$，harness $h$，轨迹 $\tau=(\sigma_0,a_0,\sigma_1,\dots)$ | $\sigma_k$ 是前缀，也就是 agent 在第 $k$ 步看到的全部信息 |
| $Y\in\{0,1\}$ | 真实成败，由环境给出 |
| $J(h)=\mathbb E_{t}\mathbb E_h[Y\mid t]$ | harness 的价值 |
| **rubric 维度** $k=(\phi_k,\ \pi_k)$ | $\phi_k(\sigma)\in\{0,1\}$ 是**在线检测器**，只读前缀；$\pi_k$ 是**干预**，也就是 $\phi_k$ 触发时对这一步 prompt 的修改（注入的 nudge），或者 harness 的动作（拦截、改写） |
| $\kappa_k=\min\{s:\phi_k(\sigma_s)=1\}$ | 维度 $k$ 第一次触发的步，即发散时刻 |
| $h\oplus k$ | 在 $h$ 上加入维度 $k$ 的触发式干预 |

## 2. 维度的价值 = 干预的因果效应（稀释定律）

在 $\kappa_k$ 之前，$h$ 和 $h\oplus k$ 的轨迹分布完全相同，因为干预还没有发生。由塔性质，在停时 $\kappa_k$ 处分解得：
$$\tau_k \equiv J(h\oplus k)-J(h)=\underbrace{P(\kappa_k<H)}_{s_k\ \text{触发率}}\cdot\underbrace{\mathbb E\big[Q^{h\oplus k}(\sigma_{\kappa_k})-Q^{h}(\sigma_{\kappa_k})\ \big|\ \kappa_k<H\big]}_{\bar a_k\ \text{触发后的平均提升}}.$$
这就是之前的稀释定律 $\tau_k=s_k\bar a_k$。它说明了三件事：
- **整体比较时的功效**：用整次评测做配对比较，方差大约是 $v_{\text{pair}}/n$，信号是 $s_k\bar a_k$。$s_k$ 小的维度，比如只在少数任务出现的错误，在整次评测里几乎测不出来。
- **局部比较的效率**：只在触发点比较（回放到 $\kappa_k$ 再分支），相对效率是 $\mathrm{RE}_k=v_{\text{pair}}/(s_k^2 f_k v_k)$。
- **V2 为什么一下子提升 10–15 个百分点**：截断 / 无代码兜底几乎在每条失败轨迹上都触发（$s$ 大），而且触发后的损失接近整条轨迹（$\bar a$ 大），两者相乘就很大。相比之下，大多数 rubric 维度的 $s_k\bar a_k$ 只有几个百分点。

## 3. 维度的有效性 = 同一任务内的 IC

在线检测器本身只是测量。它"对准了一个真实的错误"，意思是：**在同一任务内**，触发了它的尝试更容易失败。用任务固定效应模型表示：
$$\Pr(Y_{ti}=1)=\sigma(\alpha_t+\beta_k\phi_k(\tau_{ti})),\qquad H_0:\beta_k=0,$$
它的条件似然只用到"同一任务有成有败"的尝试（conditional logistic）。等价地，可以看同一任务内失败与成功的触发率差：
$$\mathrm{IC}^{\text{within}}_k=\mathbb E_t\big[\bar\phi_k^{\text{fail}}(t)-\bar\phi_k^{\text{win}}(t)\big],$$
这就是量化里"截面去均值后的 IC"：任务难度 $\alpha_t$ 相当于市场因子，被差分掉了。

**这解释了第一阶段为什么失败。** 把所有任务混在一起去学 $\Pr(Y\mid\phi)$，学到的主要是 $\mathrm{Cov}(\phi,\alpha_t)$，也就是"哪类任务难"。这在新任务族上不成立，系数甚至会反号。诊断设计的检测器之所以能迁移，是因为它们按**机制**定义，在任务内部也成立（D8：同一任务内的差值在验证集上是 +0.39）。

**统计检验**：按任务做 bootstrap 或 sign-flip，分别在 discovery 和验证集上做。只有验证集上同样成立的维度，才进入干预阶段。

## 4. 有效 ≠ 有用：从"相关"到"干预收益"

$\mathrm{IC}^{\text{within}}_k>0$ 只说明 $\phi_k$ 对准了与失败相关的状态，并不代表 $\pi_k$ 能修好它。干预收益需要满足两个条件：
$$\bar a_k>0\iff \underbrace{\text{可修复}}_{\pi_k\text{ 改变了后续行为}}\ \wedge\ \underbrace{\text{修复是正向的}}_{\text{改变后的行为让 }Q\text{ 上升}}.$$
- **操纵检验**：干预后，触发点之后的 $\phi_k$ 相关行为是否减少，比如查文档的占比、逐个处理的比率。
- **结果检验**：$\tau_k$ 用配对评测估计；对于 $s_k$ 小的维度，用回放加分支在局部估计 $\bar a_k$。

## 5. 定向的价值（触发式 vs 泛化）

令 $c(\sigma)$ 为在状态 $\sigma$ 下施加 nudge 的条件处理效应（CATE）。泛化建议等于"对所有状态都施加"，触发式等于"只在 $\phi_k=1$ 时施加"：
$$V_{\text{trig}}-V_{\text{always}}=-\,\mathbb E\big[c(\sigma)\,\mathbb 1\{\phi_k(\sigma)=0\}\big].$$
- **定向有价值 $\iff$ 在不该提醒的地方提醒是有害的**（$c<0$），比如建议过度约束、分散注意力、导致提前交卷。Dream-RSI 的消融结果（泛化的方向性建议反而变差）对应的就是 $c<0$ 的区域。
- 这把 rubric 变成了一个**处理分配规则**：最优规则是 $\mathbb 1\{c(\sigma)>0\}$；$\phi_k$ 是它的一个可解释的近似。所以 rubric 演化本质上是**策略学习 / uplift modeling**：学一个规则，决定在什么状态下给出什么 nudge。

## 6. 闭环 = 在"残差失败"上做 boosting

第 $r$ 轮的 harness 为 $h_r$。对它的失败轨迹做诊断，得到错误类别 $e$ 的"失败质量"：
$$M_r(e)=\Pr_{h_r}\big(Y=0,\ \text{decisive error}\in e\big),$$
其中 decisive error 指决定性错误。再把它分解为可回收的部分：
$$\text{headroom}_r(e)=M_r(e)\cdot \rho(e),\qquad \rho(e)=\Pr(\text{修复后成功}\mid e)\ \text{（可回收率）}.$$
下一轮选择 $e^\star=\arg\max_e \widehat{\text{headroom}}_r(e)\cdot \hat\tau(\pi_e)/\text{cost}$，写检测器加干预，用 §3–4 检验，通过就合入：$h_{r+1}=h_r\oplus k_{e^\star}$。

**与梯度提升的对应**：$-\partial\,\text{loss}/\partial F$ 的残差就是当前的失败。每一轮"拟合残差最大的那部分"，相当于选择失败质量乘以可回收率最大的错误类别；"学习率"相当于干预强度，比如 nudge 的措辞强弱、是拦截还是提示。强模型诊断扮演的是 **weak learner 的提议分布**：它提出候选 $e$ 和 $\phi_e$，统计检验负责决定是否准入。

**和第一阶段的区别**：第一阶段的 weak learner 是"拟合 $Y$ 的预测特征"，目标错了（混入了 $\alpha_t$）。现在的 weak learner 是"可以干预的机制"，目标是 $\tau$，也就是因果收益。

## 7. 可以证明的命题（按性价比排序）

1. **P1 稀释定律与局部估计的无偏性**：$\tau_k=s_k\bar a_k$；在精确回放的前提下，耦合的 IPW 估计量无偏，方差显式。（约 1 周）
2. **P2 任务内 IC 的识别**：在任务固定效应模型下，条件 logistic 对 $\beta_k$ 一致；混合目标的估计收敛到 $\beta_k+\mathrm{Cov}(\phi,\alpha)/\mathrm{Var}(\phi)$ 这类有偏量，跨任务族时偏差项会变号。这一条给第一阶段的阴性结果提供了理论解释。（约 1 周）
3. **P3 定向的价值**：上面 §5 的恒等式，加上"$\phi$ 作为 $\mathbb 1\{c>0\}$ 的分类器时，误分类代价有界"。（几天）
4. **P4 贪心闭环的单调性**：如果每轮准入都要求 $\hat\tau$ 的置信下界大于 0（用 anytime-valid 置信序列，并控制 α 预算），那么 $J(h_r)$ 以高概率单调不减，错误合入的总概率不超过 α。（1–2 周）

## 8. 估计与实验协议（已经在用的部分）

- 单元是**任务**：每个任务对多个 seed 取均值，sign-flip 检验，加 bootstrap CI。2 个 seed 时的噪声底线约 ±6.5 个百分点（同一个 F0 换 seed 的实测）。
- harness 的 bug 是**混杂因素**：每步 `evaluate()` 回滚写入、1024 token 截断、默认代码兜底。必须先清理，得到 H1，所有 $\tau_k$ 都相对干净的基线来估计。
- 预注册：每一轮的维度、干预和判定标准都在跑之前写好（A1–A9）。

## 9. 备选的数学化方向（如果当前路线效果不好）

1. **过程 reward 视角**：用回放加分支估计每一步的优势 $A(\sigma,a)$，rubric 维度作为 $A$ 的特征，准入标准是同一状态内的 IC。见之前讨论过的 $\rho\cdot\sigma_A\cdot e_n$ 收益公式。
2. **贝叶斯决策视角**：维度和干预的选择看作多臂老虎机，臂是 $(e,\pi)$，奖励是 $\tau$。用 Thompson sampling 加 top-two 分配评测预算，配合回放来降低每个臂的评估成本。
3. **低秩视角（接 AoS）**：$\Theta\in\mathbb R^{\text{task}\times\text{error}\times\text{intervention}}$，干预效应在任务和错误类别上低秩，可以借用相似任务、相似错误的信息估计 $\tau$，减少需要的评测次数。
