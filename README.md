# GateCraft

[English](README.en.md) | 中文

> 门控式数学建模 skill 套件（8 skills + DSH 预设）for DeepSeek Harness。**不无脑全流程**——agent 负责求解与质检，人在每个阶段门思考与决策，做出有自己的品味的建模结果。

## 是什么

- **8 个 skill**：`competition-workflow`（五阶段流水线：阶段门 / EDA 五问 / 验证三件套 / 脚本化验收）· `guozhan-paper`（国奖写作范式）· `vision-ocr`（读题与范文）· `sensitivity-analysis` · `statistical-diagnosis` · `math-modeling-paper` · `math-paper-template` · `tex-pdf-image-to-word`
- **assets**：`optimization-playbook`（优化类求解与验证决策表）· `figure-playbook`（流程图与图型模板）· `prompt-pack`（14 条实战提示词）· `flowchart_gen.py`（spec→drawio 生成器）· `ocr_batch.py`（并发 OCR）
- **DSH 预设**：`presets/math-modeling/`——贴入赛题即自动加载工作流

## 安装

**方式一 · DeepSeek Harness（推荐）**

```sh
dsh plugin add Cryonnan/GateCraft-math-modeling-skills
```

**方式二 · 五工具分发**（opencode / claude / codex / DSH / cc-switch）

```powershell
powershell -File .\sync.ps1
```

**方式三 · 预设（可选）**：把 `presets/math-modeling/` 复制到 `${DSH_HOME:-$HOME}/.dsh/.agent-presets/math-modeling/`，新会话选"数学建模模式"。

## 使用

> 用 competition-workflow 走流水线模式，赛题在 [路径/附件]。

流程：读题（外部指南核验+文献核验）→ 数据结构探索（EDA 五问）→ 建模（连贯链+流程图草稿）→ 求解（验证三件套）→ 灵敏度/诊断 → 七段式写作 → 脚本化验收。**阶段门是硬规则**：每问报告未通过判定标准不得进入下一问。

## 理念

- **阶段门**：每问报告自检通过才进下一问；不达标迭代 2-3 轮并记录"改动→效果→指标"
- **报告先行**：论文句子由阶段报告的事实推导，禁止照搬范文句式
- **数值纪律**：每个数字可追溯到报告或代码，改脚本重跑后零漂移核对
- **批判性核验**：外部指南逐条核验、第三方意见逐条复算、结果与文献对照
- **品味来自范式**：衔接写作四要求（R1-R4）每条附"判定标准+正面样本+反例"，范文只作样本

## 视觉能力

默认 SiliconFlow `Qwen3-VL`（key 走环境变量 `SILICONFLOW_API_KEY`，在 [cloud.siliconflow.cn/me/models](https://cloud.siliconflow.cn/me/models) 开通）；本地可用 `qwen-mm-plugins` 平替；也可改 `ocr_batch.py` 的 `BASE_URL`/`MODEL` 自接其他视觉模型。无视觉通道时，流程图走"spec→drawio/PNG→OCR 读回复核"闭环（`figure-playbook` 第 4 节）。

## 适用声明

已实战验证：**统计分析类 + 优化/决策类赛题**（一般竞赛的 C 题）。机理/物理仿真（A 类）、图论/工程（B 类）未经验证，需自行扩展检查项。

## 与 MathModelAgent

分工而非复制：它的求解器当后端（`mma_exec_python` 复现接口已预留），GateCraft 当总控与质检层——**思考、转换、深度参与发生在阶段门处**。

## 目录结构

```
skills/         8 个 skill（competition-workflow 为总控）
assets/         playbook / prompt-pack / 生成器（随 skills 同步分发）
presets/        math-modeling（DSH 预设）
sync.ps1        五工具分发脚本
index.js + cordis.patch.yml + package.json   dsh bundle 打包
```

## 创作过程（展开阅读）

<details>
<summary>四篇论文 · 三轮升级 · 每个检查项都来自一次真实翻车或一次获奖实证</summary>

**缘起。** 2023 国赛 C228（国一）说明"连贯感"来自四个机制：定位陈述、选型动机链、结果三段式、复用显式声明。2026 华数杯 C 题（作者作品）证明解题深度可在国奖线之上，但图表交叉引用错乱、缺过渡段、口径条款未进正文。泰迪杯 C 题与大湾区杯 B 题（两篇二等奖）补全七类缺陷：摘要-正文数值脱钩（"1.87%/99.2%"是正文不存在的数字）、表内列间不自洽、29 处"图表N"混用、正文残留"[GPT-5, OpenAI 计算得到]"、n=2 熵权归一化退化、5 个正类样本报 AUC、BH-FDR 概念误用。2025 国赛 C023（国一+期刊化）给出对标：每问七段式、两层流程图、先诊断后建模。GateCraft 即这些教训的固化产物。

**第一轮**：C228 连贯感 → 衔接四要求 R1-R4 + 严谨性规范；新增阶段 0.5 EDA 五问（每条发现标注"→决定哪个模型设计"）。冒烟测试用真实附件数据跑通，当场抓出论文两处口径错误（`LatestFinishHour` 并非全部 2406；"基准调度 2 个购电小时"与原始基准口径混淆）。

**第二轮**：二等论文七类缺陷 → 摘要三方对账/表内自洽/AI 痕迹扫描/方法-样本量匹配；C023 → 七段式+流程图两层规范；二手分析逐条一手核验（"PSO 分组""图1-1~1-5""21.3/28.6"全部证伪）；OCR 提速 8B 默认+32B 复核+并发 4，实测 84 页约 12 分钟（约 6 倍）。

**第三轮**：两份实战会话 → 14 条验证有效的提示词沉淀为 prompt-pack（每条带"时机/原话模板/判定标准/实测效果"）。

**踩坑细节**：流程图闭环（spec JSON→`flowchart_gen.py`→OCR 读回复核，κ→k 需归一化）；DSH 预设验证时发现 `tool-cordis` 注册进程级全局 Provider，同进程两份 cordis 系预设互斥，故预设不含自修改工具；开源审计将本地仓库与发布快照分离，发布前过"无密钥/无个人路径/无论文原文"三查。

</details>

## License

MIT。贡献 PR 请遵循统一格式：`要求 / 判定标准（可判定） / 正面样本（带页码） / 反例（带页码）`——每个检查项都必须来自真实的翻车或真实的获奖。
