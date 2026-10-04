# 干预树的因果 boosting：统一目标下的推导（v2，2026-10-05）

v1 的 §2–§6、§10 以及 BOOSTED_INTERVENTION_TREES_v0 中，残差、Newton 增益、叶子值这几样东西，大多只是**结构上类比** XGBoost。本文从**一个目标**出发把它们推导出来，并逐条说明它们和 XGBoost 一致在哪里、不同在哪里、为什么不同。

---

## 0. 记号
- 任务 $t$，harness $h$，轨迹 $\tau\sim P_h(\cdot\mid t)$，结果 $Y\in\{0,1\}$。前缀状态记为 $\sigma$。
- 状态价值 $V^h(\sigma)=P_h(Y=1\mid\sigma)$。
- **目标**：$J(h)=\mathbb E_t\,\mathbb E_{\tau\sim h}[Y]$，即期望成功率。
- **干预树** $k=(\phi_k,\pi_k)$：$\phi_k(\sigma)\in\{0,1\}$ 是只读前缀的检测器（rubric 条目），$\pi_k$ 是叶子干预（追加提示，或拦截一次）。每个 episode 只在首次触发时 $\kappa_k=\min\{s:\phi_k(\sigma_s)=1\}$ 施加一次。
- **带强度的合成** $h\oplus_\eta k$：首次触发时以概率 $\eta\in[0,1]$ 施加 $\pi_k$。$\eta$ 就是学习率，也可以理解为干预强度。

## 1. 函数梯度 = 稀释定律（精确，不是一阶近似）
**命题 1（方向导数）**
$$J(h\oplus_\eta k)-J(h)=\eta\, s_k\,\bar a_k,$$
$$s_k=P_h(\kappa_k<H),\qquad \bar a_k=\mathbb E_h\big[Q^{h\oplus k}(\sigma_{\kappa_k})-V^h(\sigma_{\kappa_k})\,\big|\,\kappa_k<H\big].$$

*证明*：在 $\kappa_k$ 之前，两种 harness 下的轨迹分布完全相同，因为干预尚未发生。到了 $\kappa_k$，以概率 $\eta$ 施加干预，此后的期望结果为 $Q^{h\oplus k}$；否则仍为 $V^h$。对 $\kappa_k$ 取条件期望即得上式。∎

于是在 harness 函数空间中，**沿干预树 $k$ 方向的梯度就是 $\tau_k=s_k\bar a_k$**，也就是 v1 的稀释定律。注意 $J$ 关于 $\eta$ 是**精确线性**的。这就是本问题和 XGBoost 的根本区别：XGBoost 可以连续地调叶子分数，而在这里，一个干预要么施加、要么不施加。

## 2. 残差从哪里来：单个状态上的分解
设干预在状态 $\sigma$ 处的作用只有两种：
- 以概率 $r_k(\sigma)$ 把一个**原本会失败**的续跑救回（rescue）；
- 以概率 $c_k(\sigma)$ 把一个**原本会成功**的续跑弄坏（harm）。

于是 $Q^{h\oplus k}(\sigma)=(1-V)r_k+V(1-c_k)$，局部优势为
$$A_k(\sigma)=Q^{h\oplus k}(\sigma)-V^h(\sigma)=\underbrace{(1-V^h(\sigma))}_{=-g(\sigma)}\,r_k(\sigma)\;-\;\underbrace{V^h(\sigma)}_{=1+g(\sigma)}\,c_k(\sigma).$$

**命题 2（残差加权）**：令 $g(\sigma)=V^h(\sigma)-1$，即 logistic 损失在目标 $y=1$ 时对 logit 的导数，则
$$\tau_k=\mathbb E\Big[\mathbb 1\{\kappa_k<H\}\big(-g(\sigma_{\kappa_k})\,r_k(\sigma_{\kappa_k})-(1+g(\sigma_{\kappa_k}))\,c_k(\sigma_{\kappa_k})\big)\Big].$$

由此可见，**残差 $g$ 是推导出来的，不是类比来的**：一棵树能带来的改进，等于它触发处的失败质量 $-g$ 乘以救回率，再减去它触发处的成功质量乘以误伤率。

- 筛选分数 value $=\rho\cdot\#(\text{触发且失败})-c\cdot\#(\text{触发且成功})$，正是把 $r_k\approx\rho$、$c_k\approx c$ 取为先验常数、并把 $V$ 换成实现值 $Y$ 之后得到的**一阶无偏估计**。
- **改进方向（v2）**：用记忆树节点的后验均值 $\hat V(\sigma)$ 代替实现值 $Y$，方差更小，并且同一前缀上的多次观测可以共享。

## 3. Hessian 从哪里来：信噪比，不是曲率
因为 $J$ 关于 $\eta$ 是线性的，所以**不存在 Newton 意义上的曲率**。$h=p(1-p)$ 出现在别处：它是二值结果的**方差**，$\mathrm{Var}(Y\mid\sigma)=V(1-V)$。

**命题 3（看哪里 = 信噪比最高的地方）**：在节点 $v$（$V_v=p$）上做成对分支，检验救回效应 $\Delta=(1-p)r$。两臂方差之和约为 $2p(1-p)=2h$（小效应近似），所以 $n$ 次配对的期望检验量为
$$\mathbb E[z^2]\approx n\,\frac{r^2(1-p)^2}{2h}=\frac{n r^2}{2}\cdot\frac{g^2}{h}.$$
因此 **$g^2/(h+\lambda)$ 就是"在该节点验证一次救回"的信噪比**。$\lambda$ 防止 $h\to 0$ 时发散：一直失败的节点，其失败本身可能是环境或 ground truth 的问题，不一定能救回。

结论：总是失败的节点（$g$ 大、$h$ 小）排在最前，原因是在那里一旦救回最容易被检验出来，而且收益最大。这正是"先看系统性错误"的统计依据。再加上 $\kappa\cdot\mathrm{sd}(p)$ 一项探索加成：观测少的节点后验不确定，值得多看。

## 4. 分裂选择：任务内的配对增益 = 条件 logistic 的得分检验
要把检测器 $\phi$ 当作**预测**失败的特征，又不能学到"这个任务难不难"，可以用带任务固定效应的模型 $\mathrm{logit}\,P(Y_{ti}=1)=\alpha_t+\beta\phi_{ti}$。用条件似然消去 $\alpha_t$ 之后，只剩同一任务内一成一败的配对 $(w,l)$，配对 logistic 损失为 $\ell=\log(1+e^{-(F_w-F_l)})$。

**命题 4**：在 $F\equiv 0$ 处，$g=-\tfrac12$，$h=\tfrac14$。XGBoost 对分裂 $\phi$ 的增益为
$$\mathrm{Gain}_{\text{within}}(\phi)=\frac{\big(\sum_{(w,l)}g\,d\big)^2}{2\big(\sum h\,d^2+\lambda\big)},\qquad d=\phi(w)-\phi(l),$$
它和 $\beta=0$ 的条件 logistic **得分检验统计量**成正比（$\lambda\to 0$ 时相等）。所以按 $\mathrm{Gain}_{\text{within}}$ 选分裂，等价于选"任务内最显著区分成败"的检测器，并且**与任务难度 $\alpha_t$ 无关**（第一阶段失败的原因正在于此，见 v1 §3）。这一部分**严格就是 XGBoost**，目标取 `rank:pairwise`。

## 5. 叶子：两个头，一个预测、一个因果
每棵树有两个叶子量，作用各不相同。

**(a) 预测头 = rubric 分数**：在第 4 节的配对损失上做 Newton 步，得到 $w_k=-G/(H+\lambda)$。把各棵树相加，就是名副其实的 **rubric 打分函数**
$$R(\tau)=\sum_k w_k\,\phi_k(\tau).$$
它衡量的是"触发这一条在多大程度上意味着会失败"，可用于给轨迹打分、作为 process reward，以及做快速评估（第 7 节）。**这部分是严格的 XGBoost。**

**(b) 因果头 = 干预价值**：$\bar a_k$ 由触发点分支（配对续跑）估计，衡量的是"在这里施加干预能修好多少"。

两者**不一定一致**：
- 预测强、因果为零的例子：P2_c01_2，在 8 个 gold 失败中命中 6 个，但它的提示让 agent 去"加引号"，结果 $\bar a=0$。
- 预测弱、因果为正的例子同样可能存在。

**准入只看因果头，打分用预测头。** 这就是"rubric"与"干预"的统一：同一组树，预测头负责打分，因果头负责行动。

## 6. 步长：悲观决策取代 Newton 步
$J$ 关于 $\eta$ 是线性的，所以 $\max_\eta$ 的解是 bang-bang 的：$\tau>0$ 时取 $\eta=1$。但 $\tau$ 是**估计**出来的，因此改为最大化**下置信界**：
$$\eta^\star=\arg\max_{\eta\in\{0\}\cup\mathcal H}\ \eta\cdot\mathrm{LCB}_{1-\alpha}(\tau_k),$$
其中 $\mathcal H$ 是可选的强度档（提示 < 拦截一次 < 强制）。这就是"下置信界 > 0 才准入"的决策论依据。

强度档之间的取舍是一个小型的 bandit。例如在 H2 分支实验中观察到，拦截一次后 agent 有时仍会再次提交同一个 id，这时可以考虑升到更强的一档。

**命题 5（单调性）**：每轮准入都要求 anytime-valid 的 $\mathrm{LCB}>0$，并按 α-spending 分配显著性预算，合入后**重新估计**已有树的效应（因为树之间存在交互：触发先后顺序、每步最多一条提示）。在这些条件下，$J(h_R)$ 以至少 $1-\alpha$ 的概率单调不降。

## 7. low-rank 快速评估（待做，接入点）
- **整轮评估**：把"任务 × harness 版本"的成功率矩阵 $M$ 视为低秩，即任务具有潜在技能、版本在这些技能上各有提升。新版本只在锚点任务上运行，其余用矩阵补全。$R(\tau)$（第 5(a) 节）可以作为补全的辅助特征。
- **分支评估**：把"候选树 × 节点"上的效应 $A_k(\sigma)$ 视为低秩张量，按第 3 节的信噪比和后验不确定性挑选下一批要分支的格子，从而减少分支次数。

## 8. 与 XGBoost 的逐项对照
| 量 | 本文推导 | 与 XGBoost 的关系 |
|---|---|---|
| 残差 $g=\hat V-1$ | 命题 2：改进 = 失败质量 × 救回率 − 成功质量 × 误伤率 | 同一个导数，意义由推导给出 |
| $h=\hat V(1-\hat V)$ | 命题 3：结果方差 → 信噪比 $g^2/(h+\lambda)$ | 公式相同，**含义不同**（方差而非曲率） |
| 分裂增益 | 命题 4：任务内配对增益 = 条件 logistic 得分检验 | **严格相同**（`rank:pairwise`） |
| 预测叶子 $w_k$ | Newton 步，加总得到 rubric 分数 $R$ | **严格相同** |
| 因果叶子 $\bar a_k$ | 命题 1：分支估计的方向导数 | **不同**（干预的效果只能测量，不能任意设定） |
| 步长 $\eta$ | 第 6 节：下置信界上的悲观决策 | 不同（线性目标；用 LCB 取代 Newton 步） |

## 9. 代码对齐（v2 需要改动的地方）
1. **value**：用记忆树节点的 $\hat V(\sigma_\kappa)$ 代替实现值 $Y$，即 $\sum_{e\in L}[(1-\hat V)\rho-\hat V c]$。
2. **rubric 打分**：为保留的树计算 $w_k$（配对 Newton 步），输出 $R(\tau)$，并报告它在 validation 上的任务内 AUC。
3. **准入**：后验或 LCB 规则（A25），并报告强度档。
4. **分支结果回写记忆树**：更新节点后验（`bit_tree --branch-meta`），供下一轮计算残差使用。
