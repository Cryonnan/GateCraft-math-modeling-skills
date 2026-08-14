---
name: math-paper-template
description: 数学建模论文 LaTeX 排版与工程 skill（只管排版，内容交给 math-modeling-paper）。覆盖 ctexart+xelatex 骨架、官方字号字体全表（黑体三号题目/宋体小四正文/单倍行距/段前段后0）、三线表、图表排版、matplotlib 中文与图字号坑、附录代码、复现验证（MCP/本地二选一）、编译交付。格式真源：../../assets/official-paper-format.md。
---

# 数模论文 LaTeX 排版与工程 skill

## 定位与分工

- **本 skill 只写排版工程**：LaTeX 骨架、字号字体、表格图注、附录代码、编译、复现验证。
- **内容与结构交给 `math-modeling-paper`**（摘要怎么写、每节写什么、严谨性审查）。
- **格式真源**：动手前先读 `../../assets/official-paper-format.md`（字号全表/三线表/图表规范）与 `../../assets/huashubei-writing-guide.md`（2026 踩坑）。
- 需要交付 Word 版：排版定稿后走 `tex-pdf-image-to-word` 路线 A，并过它的 11 条交付检查清单。

## 触发词
"数模论文""论文模板""LaTeX 论文""论文复现""section 结构""附录代码""编译""排版""三线表""图字号"

---

# 0. 工具链与通用约定

```text
编译工具: MiKTeX xelatex（...\miktex\bin\x64\xelatex.exe -interaction=nonstopmode，编译两遍）
文档类:   ctexart（12pt, a4paper）
数据/代码: 附件.xlsx/csv + run_data.py + run_q1.py...run_qN.py（每问一个脚本）
工作副本:  全英文路径（matplotlib / Jupyter 内核专用）
交付目录:  全英文路径即可（opencode 的 MathModelAgent 用 mma_create_task 生成 backend\project\work_dir\<task_id>\；其他工具自建英文目录）
```

**复现铁律**（本地 Python / MCP / Jupyter 内核通用，实测总结）：
1. work_dir 不用中文路径 → 代码内先 os.chdir(r"<全英文路径>")
2. Jupyter 内核中 sys.stdout.reconfigure() 会报错 → 直接删那两行
3. os.listdir('.') 遇中文文件名会炸 → 一律 glob.glob('*')
4. 中文绘图字体：plt.rcParams['font.sans-serif']=['SimHei']，字体文件放工作目录

---

# 1. 论文章节骨架（ctexart + 官方格式）

```latex
\documentclass[12pt,a4paper]{ctexart}
\usepackage[top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm]{geometry}  % 华数杯/国赛四边2.5cm
\usepackage{amsmath,amssymb,amsfonts,mathtools}
\usepackage{graphicx,booktabs,multirow,float,caption,listings,xcolor}
\usepackage[hidelinks]{hyperref}
\usepackage{indentfirst}\setlength{\parindent}{2em}   % 首行缩进2字符
\pagestyle{plain}           % 【硬坑】ctexart 默认 headings 页眉显示"节名+页码"，官方模板无页眉，必须 plain
% 标题层级：一级黑体四号居中 / 二级黑体小四左对齐 / 三级宋体小四左对齐（华数杯官方）
\ctexset{
  section = {format = {\heiti \zihao{4} \centering}},
  subsection = {format = {\heiti \zihao{-4}}},
  subsubsection = {format = {\songti \zihao{-4}}},
}
\renewcommand{\thefigure}{\arabic{figure}}   % 全文连续编号（表/图不按章）
\renewcommand{\thetable}{\arabic{table}}
```

正文顺序：
```text
题目（黑体三号居中）+ 摘要（"摘要"黑体四号居中；内容宋体小四单倍行距、≤1页）
\section{问题重述}        → 1.1 问题背景 / 1.2 问题回顾（≤1页，自组织语言）
\section{问题分析}        → 每问一个 \subsection；禁结果
\section{模型假设}         → 4-8条（三来源）
\section{符号说明}         → 三线表（符号|说明|单位），约半页不换页
\section{数据预处理}       → 筛选/清洗/特征工程/EDA
\section{问题一~N}          → 每问：\subsection{模型建立/模型求解/模型检验}
\section{灵敏度分析}        → 数据来自 SENSITIVITY_REPORT.md
\section{模型评价与推广}
\clearpage \section*{参考文献}     % 另起一页（排版层加 \clearpage）
\clearpage \appendix \section{附录} % 另起一页；A 支撑材料 / B 结果明细 / C 完整代码
\end{document}
```

结构红线：全文只一次 \begin{document}；每问固定三段（建立/求解/检验）；附录代码与 run_*.py 逐行一致（行号累计校验）；公式全文统一连续编号。

## 字号字体对照表（真源 official-paper-format.md 二）

| 元素 | 字体 | 字号 | LaTeX 落实 |
|------|------|------|-----------|
| 题目 | 黑体 | 三号(15pt) | `{\heiti\zihao{3} 题目}` 居中 |
| "摘要" | 黑体 | 四号(14pt) | `{\heiti\zihao{4} 摘~~~要}` 居中 |
| 摘要内容/正文 | 宋体+TNR | 小四(12pt) | 默认，**单倍行距、首行缩进2字符、段前段后0**（勿加 \onehalfspacing） |
| 一级标题 | 黑体 | 四号(14pt) | ctexset section |
| 二级标题 | 黑体 | 小四(12pt) | ctexset subsection |
| 三级标题 | 宋体 | 小四(12pt) | ctexset subsubsection |
| 表格文字 | 宋体 | 五号(10.5pt) | \zihao{5} |
| 表题/图题 | 黑体 | 五号(10.5pt) | 表题在上、图题在下，居中 |

---

# 2. 图表排版规范（血泪实测）

## 2.1 图字号【最大硬坑：图大字小】
- 最终打印字号 ≈ matplotlib 字号 × (显示宽 ÷ 图物理宽)；图物理宽 = 像素 ÷ dpi。
- figsize 宽 ≈ 最终显示宽：0.92\textwidth≈5.8in、0.85\textwidth≈5.4in；dpi≥200。
- 图内字号 base 10.5–11pt（≈正文五号），标题 12–13pt；合格判据：保存字号×缩放比 ≥9pt。
- **禁用 bbox_inches=tight**（+constrained_layout 会把 5.8in 画布放大到 9.9in、字更小）→ 固定 figsize×dpi 输出，白边由 LaTeX 图宽吸收。
- PIL 缩放像素无法拯救栅格化字号，必须按"显示宽→figsize 映射表"重新渲染。
- 验证：编译 PDF 后截图放大看坐标轴数字（模型不支持图片时用 vision-ocr 看）。

## 2.2 三线表与表注（booktabs）
- \toprule(1.5pt) \midrule(0.75pt) \bottomrule(1.5pt)；允许辅助线。
- 表号表题在上居中（表1 表题）、图号图题在下居中；正文先引后出（凡引必见）。
- 表内单位写列头「量/单位」；符号说明表固定三栏（符号|说明|单位）。
- **特殊值必须 * + 表注**：负值（注"负号表示…"）、0 值（注"0 表示…"）、负 R²（注"预测弱于序列均值"）、恒定量（正文如实说明）。

## 2.3 中文字体与上标渲染
matplotlib 用 R²（U+00B2）→ SimHei 无该字形显示方块。修复：凡 ²/³/下标一律 mathtext：
```python
label='OLS ($R^2$=%.3f)'   # 而非 'OLS (R²=%.3f)'
plt.text(..., r'$S^2_u$=%.4f', ...)
# 单位同理 kg/m$^2$；σ_u² 写 $\sigma^2_u$
```

---

# 3. 附录代码规范（lstlisting）

```latex
\lstset{ % 附录前，紧凑模式
  basicstyle=\footnotesize\ttfamily, numbers=left, numberstyle=\tiny\color{gray},
  frame=single, breaklines, showstringspaces=false, keywordstyle=\color{blue},
  upquote=true, columns=flexible,
}
\subsection{完整代码}
\lstinputlisting{run_data.py}   % 依次 run_data/run_q1/.../run_qN
```
禁忌：caption 里 _ 必须转义 \texttt{run\_q1.py}（否则 Missing $ inserted）；禁 # ... 占位符进附录；附录行号累计 == ∑各 run 脚本行数。

---

# 4. 复现验证流程（写论文必须过，MCP / 本地二选一）

**能力探测**：环境有 MathModelAgent MCP（mma_create_task / mma_exec_python）走 4A，否则（claude/codex/DSH 等）走 4B 本地 Python，步骤等价。

**4A（有 MCP）**
1. mma_create_task → 英文路径工作目录；2. 数据+全部 run_*.py 拷入；3. 每个 run_q*.py 用 mma_exec_python 单独复现（session_id 固定）；4. 逐段核对 tex 关键指标与代码输出一致（列出核对表）；5. 图有改动复制回 tex 目录；6. 编译 PDF 校验。

**4B（无 MCP，本地 Python）**
1. 建全英文工作目录并 os.chdir；2. 数据+run_*.py 拷入；3. 逐个 python run_q*.py，数值/图/表落盘；4-6 同 4A（核对表、图回拷、编译校验）。

---

# 5. 编译与交付

- 编译：xelatex -interaction=nonstopmode <主文件> 两遍（交叉引用/目录）。
- 交付物：PDF + tex + 全部 run_*.py（下载链接）。版本命名：保留基底版本号（paper_v_final.pdf）。
- 交付前跑 `competition-workflow` 的提交前检查清单（无页眉/2.5cm/页码从1/≤30页/图字号/表注/零漂移/AI声明）。
- 需要 Word 版 → `tex-pdf-image-to-word`（路线 A 转 docx 或路线 B 重建），并过 11 条检查。

# 6. 复用方式

把本骨架当基底，改章节名/问题描述/方法链，结构不动；数据与代码放英文路径后走第 4 节复现流程。内容写作规范一律查 `math-modeling-paper`。

