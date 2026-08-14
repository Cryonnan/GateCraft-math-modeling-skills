---
name: statistical-diagnosis
description: 统计诊断流水线（统计学博士视角审校）。Step 0 先读题面和实际代码/结果报告再选诊断路径（横截面/时序/面板/事件研究/ML），含多重比较校正、效应量报告、假设验证、Bootstrap BCa。产出 DIAGNOSIS_REPORT.md 供论文与验收阶段引用。与 sensitivity-analysis 分工：诊断=模型对不对，灵敏度=结论稳不稳。
---

# 统计诊断流水线（统计学博士审校版）

## 触发词
"显著性检验""异方差""自相关""多重共线性""单位根""ADF""协整""Johansen""Granger""Breusch-Pagan""Durbin-Watson""White检验""VIF""ARCH效应""Corrado""Patell""BMP""效应量""多重比较校正""BH-FDR""Bonferroni"

## Step 0：先读题，再选路径（不要无脑跑全套）

诊断是对**实际模型**的检验，不是知识问答。开工前必须拿到三样东西：
1. 题面/建模报告（判断题型与数据结构）；
2. 实际代码与数据（残差、拟合值、时间索引）；
3. RESULTS_REPORT.md（若在流水线中）。

然后按决策树**只走一条路径**：
```
数据类型：
├── 横截面   → 残差图→BP(异方差)+VIF(if k>1)+JB/SW(正态)+DW跳过(无时序)
├── 时间序列 → ADF+KPSS联合→(非平稳则差分)→协整(Johansen)→Granger(报滞后阶数)→ARCH(收益率类)
├── 面板     → Hausman→FE/RE→聚类稳健标准误
├── 事件研究 → 事件日聚集诊断→JB→Corrado+BMP+Bootstrap(BCa CI)
└── ML预测   → Nested CV→置换检验→Cohen's d→残差诊断
```
每走一步都把**检验的适用前提**与本题核对一遍（见各类型"先验证假设"）。

## 全局统计准则

**准则1：p 值不可单独报告。** 每次报告 = ①效应量 ②p 值/CI ③实质性结论。
✅ "因子与 CAR 的 Spearman ρ=0.401，p<0.001，表明网络传导效应与异常收益存在中等正相关"；❌ "p<0.001，显著"。
**准则2：多重比较必须校正。** 并行检验 m≥2 → BH-FDR（`校正p = min(p_raw×m/rank(p), 1)`）或 Bonferroni（`α'=0.05/m`）。
**准则3：检验前先验证假设。** T 检验前查样本独立性；BP 前先画残差图；ADF 前目视趋势/季节；VIF 前确认 k>1。
**准则4：大样本 p 值陷阱。** N>10,000 时 p 几乎必 <0.001，改用效应量 + CI + 性能增量（RMSE/MAE）。
**准则5：产出 DIAGNOSIS_REPORT.md。** 论文与验收阶段的数值只从本报告取；改脚本重跑后与论文数字核对零漂移。

---

# 类型 A：回归模型诊断

```
Step 0: 画残差 vs 拟合值散点图（目视模式）
Step 1: Shapiro-Wilk（n<2000）/ Jarque-Bera（大样本）正态性
Step 2: Breusch-Pagan 异方差（先有残差无系统模式的观察）
Step 3: Durbin-Watson 自相关（仅时序结构数据；横截面跳过）
Step 4: VIF 共线性（仅 k>1；LASSO/Ridge 已正则化则跳过）
Step 5: 并行检验 m≥2 → BH-FDR 校正
```

| 检验 | 统计量 | 严格阈值 | 宽松阈值 | 处理方案 |
|------|--------|---------|---------|---------|
| BP | LM stat | p<0.01 | p<0.05 | HC3 稳健标准误或 WLS |
| DW | d∈[0,4] | d<1.5 或 d>2.5 | d<1.8 或 d>2.2 | Newey-West 或 GLS-AR(1) |
| VIF | max VIF | >10 | >5 | 删变量或 PCA/岭回归 |
| JB/SW | stat | p<0.01 | p<0.05 | n>100 可依 CLT 放宽 |

不适用跳过：Logistic 用 Hosmer-Lemeshow（不用 BP）；横截面不用 DW；正则化模型不用 VIF。

# 类型 B：时间序列诊断

ADF+KPSS 联合决策矩阵：
```
            KPSS不拒绝H0        KPSS拒绝H0
ADF拒绝H0   平稳 ✅             结论冲突 → 差分+重检
ADF不拒绝   结论冲突 → 差分     非平稳 → 差分处理
```
- ADF 最大滞后：`int(12×(n/100)^(1/4))`（Schwert 准则）；Johansen 用 AIC/BIC 扫 lag=1~12；Granger 必须报所选滞后阶数及依据。
- ARCH 检验仅用于收益率等波动率聚类序列；有 ARCH 效应 → GARCH(1,1) 作稳健性检验。

# 类型 C：事件研究诊断

CAR 分布决策树：
```
正态（JB p>0.05）→ 参数 T 检验 + Patell Z
非正态 + n>1000 → Corrado 秩检验（首选）+ BMP 横截面检验
非正态 + n<200 → Wilcoxon 符号秩检验
截面相关 → BMP（标准化残差法）
```
- **Corrado 局限（必查）**：事件日高度聚集（某日事件 > 总事件 5%）时秩次不独立、检验膨胀 → 先做聚集性诊断，必要时换 BMP。
- Bootstrap CI 用 BCa（偏差校正+加速因子，jackknife 估计 a），分布偏斜时优于分位数法。

# 类型 D：面板 / ML 诊断（速查）

- 面板：Hausman 检验 → FE/RE → 公司/时间双聚类稳健标准误。
- ML：Nested CV（外循环调参、内循环评估，禁止测试集调参）→ 置换检验 → Cohen's d；时序必须 TimeSeriesSplit。

---

# 诊断报告输出（DIAGNOSIS_REPORT.md，紧凑版）

```markdown
### [模型名称] 诊断摘要
| 检验 | 统计量 | p值(校正后) | 效应量 | 结论 |
|------|--------|------------|--------|------|
| BP异方差 | LM=XX | 0.XX | - | 同方差/异方差 |
| DW自相关 | d=X.XX | - | - | 无自相关 |
| VIF共线性 | max=X.X | - | - | 无共线性 |
| JB正态性 | JB=XX | 0.XX | skew=XX | 非正态(n大忽略) |
处理建议：[一句话，落到代码修改动作]
```

# 与 sensitivity-analysis 的分工（防止重复劳动）

- **本 skill（诊断）**：模型假设成立吗？（残差/共线/平稳/聚集性）→ 不成立就修模型或换估计方法。
- **sensitivity-analysis**：模型结论稳吗？（参数扰动下结果变不变）→ 报告稳健性。
- 流水线顺序：阶段 2 建模后先诊断（修正模型）→ 阶段 3 再灵敏度（结论稳健性）→ 两份报告都被论文和验收引用。

