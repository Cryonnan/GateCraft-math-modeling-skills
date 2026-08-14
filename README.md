# GateCraft（门控工艺）· 数学建模模式 for DeepSeek Harness

**门控式数学建模 skill 套件 + DSH 预设**：把全国大学生数学建模竞赛的完整解题与写作方法论，固化为可复用的检查项工作流——**不无脑全流程，让每个阶段门都有证据、可判定、可人工干预**。

> 宗旨：agent 负责求解与质检，**人负责在阶段门处思考、转换、深度参与**。全自动出论文的流水线会把假 Pareto、口径错位、摘要-正文数值脱钩这类硬伤埋进终稿；本项目的每个检查项都来自对四篇实战论文（含两篇国奖范文与两篇二等奖论文）的逐页复盘。

## 创作过程与理念（写在前面）

**缘起——四篇论文，四个教训。** 2023 国赛 C228（蔬菜定价，国一）说明"连贯感"来自四个机制：每问开头的定位陈述、选型动机链（先简后繁+试错叙事）、结果三段式（数值→机制→外部互证）、复用显式声明。2026 华数杯 C 题（我们自己的作品）证明解题深度可以在国奖线之上，但图表交叉引用错乱（图13/图11/表10）、缺过渡段、口径条款未进正文——"割裂感"不在建模，在衔接层。泰迪杯 C 题与大湾区杯 B 题（两篇二等奖）把缺陷清单补成七类：摘要与正文数值脱钩（"1.87%/99.2%"是正文不存在的数字）、表内列间不自洽（λ 与半衰期对不上）、"图表N"混用 29 处、正文残留"[GPT-5, OpenAI 计算得到]"、n=2 上做熵权归一化、5 个正类样本报 AUC、BH-FDR 概念误用。2025 国赛 C023（NIPT，国一+期刊化）给出最终对标：每问七段式、两层流程图、先诊断后建模（热力图→排除线性→二次项）、"未使用 AI 技术"的合规披露。**GateCraft 就是把这四篇论文的教训逐条固化成检查项的产物。**

**理念——在 agent 运行中思考，做出有自己的品味的建模结果。** 四篇论文证明：全自动流水线恰恰把最致命的错误埋进终稿，而这些错误没有一个是"模型不够强"，全部是"没人停下来看一眼"。因此 GateCraft 不取代人，而是把"停下来看一眼"制度化为五项检查：**阶段门**（每问报告自检通过才进下一问，不达标迭代 2-3 轮并记录"改动→效果→指标"）；**报告先行**（论文句子由阶段报告的事实推导，禁止照搬范文句式）；**数值纪律**（每个数字可追溯到报告或代码，零漂移核对）；**批判性核验**（外部指南逐条核验、第三方意见逐条复算、结果与文献对照——"他说的是不是对的"永远是第一问题）；**品味来自范式、不来自套模板**（衔接写作四项要求 R1-R4 每条都附"判定标准+正面样本+反例"，范文原句只作样本）。最终论文的品味——连贯、克制、每张图服务一个决策点——来自这套门控，而不是某一次 prompt 的运气。

**从素材到产品，共三轮升级。** 第一轮把 C228 的连贯感变成检查项：提炼衔接四要求 R1-R4 与严谨性用语规范，并在 competition-workflow 中新增**阶段 0.5 数据结构探索（EDA 五问）**——每条发现必须标注"→决定了哪个模型的哪个设计"；冒烟测试用真实附件数据跑通，当场抓出论文的两处口径错误（`LatestFinishHour` 并非全部 2406、"基准调度 2 个购电小时"与原始基准口径混淆），这正是"口径审计"环节存在价值的实证。第二轮把二等论文的七类缺陷变成硬检查（摘要三方对账、表内自洽、AI 痕迹扫描、方法-样本量匹配），把 C023 变成七段式+流程图两层规范；同时对二手分析做了逐条一手核验——"PSO 分组""图1-1~1-5""21.3/28.6"等具体细节全部证伪，确立"只信官方页面图+OCR 文本，不信二手复述的具体数字"的采信原则；并把 OCR 从串行 32B 提速为 8B 默认+32B 复核+并发 4 线程，实测 84 页约 12 分钟（约 6 倍）。第三轮复盘两份实战会话，把 **14 条被验证有效的提示词**沉淀为 prompt-pack（外部指南核验、文献 DOI 不编造、阶段门、性能门槛、第三方诊断复算……），每条带"时机/原话模板/判定标准/实测效果"。

**工具链的每个细节都来自踩坑。** 无视觉模型如何验收流程图？流程图草稿写成 spec JSON → `flowchart_gen.py` 确定性生成 `.drawio`/`.mmd`/`.png` → vision-ocr 8B 读回 → 与 spec 逐项比对（实测 16/16、15/16 项命中，唯一"未命中"是 κ 被 OCR 读成拉丁 k，比对时做希腊字母归一化即可）。DSH 预设"数学建模模式"的诞生也踩了一个真实的坑：从创造模式复制改人设后挂载验证报错——`tool-cordis` 注册进程级全局 Provider，同进程内两份 cordis 系预设互斥，最终版移除自修改工具、保留完整建模工具链。开源审计则把本地仓库与发布快照彻底分离：本地保留原样，发布前过"无密钥/无个人路径/无论文原文"三查。

**适用边界。** ✅ 已实战验证：统计分析类（预测/回归/事件研究/判定）与优化/决策类（调度/配置/定价）赛题——即一般数学建模竞赛的 **C 题**（2023C 蔬菜、2024C 种植、2025C NIPT、华数杯 C 算电协同、泰迪杯 C 事件驱动；评价类仅以大湾区杯 B 题子模块覆盖）。⚠️ 未经验证：机理/物理仿真类（A 类）、图论/工程结构类（B 类）——使用时需自行扩展决策树与检查项，并把扩展经验回馈本项目。

**如何贡献你的"品味"。** 发现新的缺陷模式或更优的检查项时，按统一格式提交 PR：`要求 / 判定标准（可判定） / 正面样本（带页码） / 反例（带页码）`。这是 GateCraft 自我进化的方式——**每个检查项都必须来自真实的翻车或真实的获奖，不接受凭空想象的建议。**

## 组成

```
skills/                    # 8 个 skill（跨 opencode/claude/codex/DSH/cc-switch 五工具）
  competition-workflow/    # 总控：五阶段流水线 + 阶段门 + EDA五问 + 验证三件套 + 脚本化验收
  guozhan-paper/           # 国奖写作范式：每问七段式 + 衔接四要求(R1-R4) + 严谨性规范 + 流程图两层规范
  vision-ocr/              # 读题/读范文：8B 提速 + 32B 关键页复核 + 断点续传
  sensitivity-analysis/    # 灵敏度引擎（题型自适应）
  statistical-diagnosis/   # 统计诊断流水线
  math-modeling-paper/     # 内容规范与严谨性审查
  math-paper-template/     # LaTeX 排版工程
  tex-pdf-image-to-word/   # Word 交付路线
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

本仓库是标准 dsh 插件包（`package.json` 含 `dsh.bundle` 清单 + `cordis.patch.yml` + `index.js` 注册全部 8 个 skill）：

```sh
# 通过 dsh 插件市场图形界面搜索 "gatecraft" 安装，或命令行：
dsh plugin add gatecraft                    # npm 发布后
# 或直接从 git 安装：
dsh plugin add Cryonnan/GateCraft-math-modeling-skills
```

安装后 8 个 skill 随 profile 生效，无需手动复制到 `.agents/skills`。`presets/math-modeling/` 预设为可选增强（复制到 `${DSH_HOME:-$HOME}/.dsh/.agent-presets/math-modeling/` 后可让新会话自动进入建模工作流）。

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

创作过程、每轮升级的细节与踩坑记录见上文「创作过程与理念」一节。

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
- [Cryonnan/GateCraft-math-modeling-skills](https://github.com/Cryonnan/GateCraft-math-modeling-skills) - GateCraft（门控工艺）：门控式数学建模 skill 套件（8 skills + DSH 预设）——五阶段流水线、阶段门、国奖写作范式、流程图 spec→drawio 生成与 OCR 复核闭环。
```

## License

MIT（见 [LICENSE](LICENSE)）。欢迎 PR：新检查项、新题型模板、新实证页码引用——提交格式见上文「创作过程与理念」之「如何贡献」。
