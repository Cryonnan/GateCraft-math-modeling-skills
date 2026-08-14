# 数学建模模式（Math Modeling Mode for DeepSeek Harness）

**门控式数学建模 skill 套件 + DSH 预设**：把全国大学生数学建模竞赛的完整解题与写作方法论，固化为可复用的检查项工作流——**不无脑全流程，让每个阶段门都有证据、可判定、可人工干预**。

> 宗旨：agent 负责求解与质检，**人负责在阶段门处思考、转换、深度参与**。全自动出论文的流水线会把假 Pareto、口径错位、摘要-正文数值脱钩这类硬伤埋进终稿；本项目的每个检查项都来自对四篇实战论文（含两篇国奖范文与两篇二等奖论文）的逐页复盘。

## 组成

```
skills/                    # 9 个 skill（跨 opencode/claude/codex/DSH/cc-switch 五工具）
  competition-workflow/    # 总控：五阶段流水线 + 阶段门 + EDA五问 + 验证三件套 + 脚本化验收
  guozhan-paper/           # 国奖写作范式：每问七段式 + 衔接四要求(R1-R4) + 严谨性规范 + 流程图两层规范
  vision-ocr/              # 读题/读范文：8B 提速 + 32B 关键页复核 + 断点续传
  sensitivity-analysis/    # 灵敏度引擎（题型自适应）
  statistical-diagnosis/   # 统计诊断流水线
  math-modeling-paper/     # 内容规范与严谨性审查
  math-paper-template/     # LaTeX 排版工程
  tex-pdf-image-to-word/   # Word 交付路线
  linear-regression-hw/    # 回归分析作业助手
assets/                    # 决策表与生成器（随 skills 同步分发）
  optimization-playbook.md # 优化类求解降级链/验证三件套/多目标前沿诊断（华数杯 C 题实测）
  figure-playbook.md       # 流程图两层模板 + 图型模板 + 规格→drawio 生成链路
  prompt-pack.md           # 14 条实战验证的提示词（按比赛阶段复制使用）
  flowchart_gen.py         # 流程图生成器：spec JSON → .drawio/.mmd/.png（零依赖）
  ocr_batch.py             # 通用批量 OCR（并发+双档+降级+续传）
presets/math-modeling/     # DSH agent preset（数学建模模式：人设+自动触发 competition-workflow）
sync.ps1                   # 一键分发到 5 个工具目标（$HOME 自动探测，fork 即可用）
```

## 快速开始

### 0. 一键安装（DeepSeek Harness 插件市场 / dsh plugin add）

本仓库是标准 dsh 插件包（`package.json` 含 `dsh.bundle` 清单 + `cordis.patch.yml` + `index.js` 注册全部 9 个 skill）：

```sh
# 通过 dsh 插件市场图形界面搜索 "math-modeling" 安装，或命令行：
dsh plugin add math-modeling-skills        # npm 发布后
# 或直接从 git 安装：
dsh plugin add <你的GitHub用户名>/<仓库名>
```

安装后 9 个 skill 随 profile 生效，无需手动复制到 `.agents/skills`。`presets/math-modeling/` 预设为可选增强（复制到 `${DSH_HOME:-$HOME}/.dsh/.agent-presets/math-modeling/` 后可让新会话自动进入建模工作流）。

### 1. 手动安装 skills（跨 opencode/claude/codex/DSH/cc-switch 五工具）

```powershell
# Windows PowerShell：仓库根目录执行，一键分发到全部 5 个工具
powershell -File .\sync.ps1

# 或只装 DSH：
powershell -File .\sync.ps1 -Targets agents
```

DSH/agents 目标热更新；其余工具重启会话后生效。sync.ps1 参数：`-Targets`（只同步指定目标）、`-DryRun`（预览）、`-Prune`（删除孤儿目录）、`-Commit`（自动 git 提交）。

### 2. DSH 用户：挂载"数学建模模式"预设

把 `presets/math-modeling/` 复制到 `${DSH_HOME:-$HOME}/.dsh/.agent-presets/math-modeling/`，新会话选择该预设即可。该预设自带建模人设，**贴入赛题即自动加载 `competition-workflow` 并按五阶段流水线执行**（阶段门守门、数值纪律、报告先行）。

### 3. 使用

对 Agent 说（或直接贴赛题 PDF 路径）：

> 用 competition-workflow 走流水线模式，赛题在 [路径/附件]。

流程自动执行：读题（含外部解题指南逐条核验 + 文献 DOI 核验）→ 数据结构探索（EDA 五问，每条发现标注"→决定哪个模型设计"）→ 每问建模（连贯链 + 流程图草稿 spec）→ 求解（验证三件套 + 性能门槛）→ 灵敏度/诊断 → 七段式写作 → 阶段 5 脚本化验收（摘要三方对账/图表编号/表内自洽/AI 痕迹扫描）。

**阶段门是硬规则**：每问报告未通过判定标准不得进入下一问；不达标子问题迭代 2-3 轮并记录"改动→效果→指标"。

## 视觉能力（无视觉模型的环境怎么读图）

本套件默认的视觉通道是 SiliconFlow 的 Qwen3-VL 系列，**API key 一律通过环境变量提供，仓库不含任何密钥**：

```powershell
$env:SILICONFLOW_API_KEY = "你的key"   # 在 https://cloud.siliconflow.cn/me/models 开通
```

- 推荐模型：`Qwen3-VL-8B-Instruct`（批量提速，约 15-25s/页）+ `Qwen3-VL-32B-Instruct`（表格数字/流程图/公式密集页复核，约 50-90s/页）；并发 4 线程实测 84 页约 12 分钟。
- **本地平替**：装 `qwen-mm-plugins`（本地多模态插件：读图/裁剪/标注/渲染），把需要"看"的内容落盘后仍由 `vision-ocr` 的云端模型识别——两者互补。
- **自接其他视觉模型**：改 `skills/vision-ocr/SKILL.md` 模板与 `assets/ocr_batch.py` 顶部的 `BASE_URL`/`MODEL` 即可（OpenAI 兼容接口）。
- 无任何视觉通道时的兜底：流程图走"规格→drawio/PNG 生成→OCR 读回复核"闭环（见 `figure-playbook.md` 第 4 节），不靠眼睛也能验收。

## 适用声明（务必先读）

本流程的**训练与实战验证范围**：统计分析类 + 优化/决策类赛题——即一般数学建模竞赛的 **C 题**（2023C 蔬菜定价、2024C 种植、2025C NIPT、华数杯 C 算电协同、泰迪杯 C 事件驱动、大湾区杯 B 稳定币）。机理/物理仿真类（A 类）、图论/工程结构类（B 类）**未经实战验证**，使用时需自行扩展决策树与检查项。

完整创作过程、每轮升级的细节与踩坑记录见 **[CREATION.md](CREATION.md)**。

## 与 MathModelAgent 的关系：协作，不复制

[MathModelAgent](https://github.com/jihe520/MathModelAgent)（3455★）是"自动完成建模、直接出可提交论文"的全流程 agent，求解机制齐全。本项目与它的分工：

```
人（在每个阶段门做决策）
  └─ competition-workflow 总控（本仓库）——门控 / 质检 / 写作 / 验收
       ├─ 阶段 0.5 EDA 五问、阶段 5 脚本化对账（本仓库独有的质检层）
       └─ 阶段 2 求解：可调用任何求解器，或 MathModelAgent 的 MCP（mma_exec_python）
```

它的求解器与本项目的总控/质检层互补：检查清单中已预留接口（"有 MathModelAgent MCP 则用 `mma_exec_python` 复现"）。**推荐用法：它跑求解，我们跑门控与质检；思考、转换、深度参与发生在阶段门处。**

## 技能协作图（数模一条龙）

```
                    competition-workflow（总控，两模式：流水线 / Day1-3 时间线）
                              │ 阶段0 读题（OCR + 外部指南核验 + 文献核验）
                              ▼
                         vision-ocr（OCR 落盘，按需取段）
                              │ 阶段0.5 数据结构探索（EDA 五问 → 每条发现标注下游设计）
                              │ 阶段1 分析建模（连贯链 + 流程图草稿 spec）→ ANALYSIS_MODELING_REPORT.md
                              │ 阶段2 代码结果（验证三件套 + 性能门槛）→ RESULTS_REPORT.md
                              │     └─ statistical-diagnosis（模型诊断 → DIAGNOSIS_REPORT.md）
                              │ 阶段3 灵敏度 → sensitivity-analysis（题型自适应 → SENSITIVITY_REPORT.md）
                              │ 阶段4 论文
                              ▼
          math-modeling-paper（内容） ──► math-paper-template（排版） ──► PDF
                 │ 参考 guozhan-paper（国奖范式）       │ 需要 Word 版
                 └── official-paper-format.md ◄────────┴──► tex-pdf-image-to-word（11 条检查）
                              │ 阶段5 验收（脚本化对账 + 外部诊断复算 + 文献一致性）→ VERIFY_REPORT.md
                              ▼
                          提交前检查清单（★项逐条勾验）
```

**数值纪律**：论文每个数字只许来自 reports/ 报告或代码输出；改脚本重跑后做「论文数字↔报告」零漂移核对。

## 证据与免责

- 全部范式来自公开获奖论文的**页码引用与结构化提炼**（2023 C228、2024 C038、2025 C132/C023 等），仓库不含任何论文原文、页面图或提取全文；
- 反例证据均为"事实陈述+页码"，不附带他人论文内容；
- 实测数字（如华数杯 C 题 RMSE 96.06）为可公开的结果数据。

## 收录与投稿状态

- 仓库添加 topics：`dsh-plugin`、`deepseek-harness`、`math-modeling`、`skills`、`cumcm` → 自动出现在 [GitHub dsh-plugin 话题页](https://github.com/topics/dsh-plugin)。
- 投稿 [awesome-dsh-plugin](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin) 精选列表：PR 在 `README.md` 与 `README.zh.md` 的 `### Skills` 分类下各加一行：

```markdown
- [<your-name>/math-modeling-skills](https://github.com/<your-name>/math-modeling-skills) - 门控式数学建模 skill 套件（9 skills + DSH 预设）：五阶段流水线、阶段门、国奖写作范式、流程图 spec→drawio 生成与 OCR 复核闭环。
```

## License

MIT（见 [LICENSE](LICENSE)）。欢迎 PR：新检查项、新题型模板、新实证页码引用——提交格式见 [CREATION.md](CREATION.md) 第四节。
