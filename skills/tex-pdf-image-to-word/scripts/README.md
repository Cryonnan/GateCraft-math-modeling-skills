# 文档/公式/图片转 Word 脚本库

将 **tex / PDF / 图片** 转换为排版准确的 Word 文档（公式可编辑 OMML）的一站式脚本集。

## 两种转换路线

| 输入类型 | 路线 | 入口脚本 | 适用场景 |
|---|---|---|---|
| LaTeX 源码 (.tex) | **路线A：直接转换** | `tex_to_docx.py` | 有 .tex 源码的数模论文/学术文档 |
| 纯图片 PDF（无文本层）/ 图片型 PDF | **路线B：OCR 重建** | `pdf_image_to_docx.py` | 扫描件、课件截图、公式多图像多的 PDF |
| 单张图片 / 任意 PDF（仅识图） | 辅助工具 | `vision_qwen.py` | 识图、提取文本/图表数据、提取内嵌图 |

---

## 路线A：tex → Word（直接转换）

```bash
python tex_to_docx.py input.tex [reference.docx|dotx] [output.docx]
```

流程：图片修复（tex 引用缺失的图片自动从同目录 PDF 提取）→ 预处理剥离 ctexart 版式命令 / 图表格公式编号文本化 / `\ref` `\cite` 解析 → pandoc（公式转 Word 原生 OMML 可编辑）→ 后处理套模板样式（宋体/黑体/行距/缩进/三线表/页码）→ 结构验证。

依赖：pandoc、python-docx、PyMuPDF。

## 路线B：纯图片 PDF → Word（OCR 重建）

```bash
python pdf_image_to_docx.py input.pdf [--ref ref.docx] [--out out.docx] [--no-ocr] [--img-map "..."]
```

流程（6 步）：
1. 渲染 PDF 每页为 PNG（dpi=150）
2. **Qwen3-VL 视觉模型逐页 OCR** → Markdown（数学公式 LaTeX，图片占位 `[图N]`）
3. 提取 PDF 内嵌图片（`p{i}_img{j}.png`）
4. 自动/手动建立图片映射（页号, 图号 → 文件名+显示宽度）
5. 组装 `combined.md` + 清洗（修复 `$` 前空格等 pandoc 数学定界问题）→ pandoc 转 docx（公式 OMML 可编辑）
6. 验证输出（段落/表格/图片/OMML 公式数）

**图映射说明**：默认 `auto_map_imgs` 按页内 `[图N]` 顺序对应 `p{page}_img{N}.png`；若错位可在脚本顶部 `IMG_MAP` 手动指定：

```python
IMG_MAP = {
    (3, 1): ('p3_img3.png', '9cm'),   # 第3页第1个图 -> 坐标系题图, 宽9cm
    (3, 2): ('p3_img6.png', '12cm'),  # 第3页第2个图 -> 正弦函数图像
    (4, 1): ('p4_img5.png', '11cm'),
}
```

也可用 `--img-map '(3,1):["p3_img3.png","9cm"]; (4,1):["p4_img5.png","11cm"]'` 命令行传入（键 `(页号,图号)`，值 `(文件名,宽度)`；PowerShell 下注意引号转义）。

**已踩坑（勿重复）**：
- OCR 常输出 `= $（ ）`（`$` 前空格）→ pandoc 不识别为数学定界符，公式源码泄漏成 `$(-13^) = $`。脚本已自动清洗（`re.sub(r'[ \t]+\$', '$', ...)`）。
- pandoc 3.9 不支持 `{\bfseries ...}` 组语法（输出字面 "bfseries"），tex 里需用 `\textbf`。
- pandoc 相对图片路径按进程 CWD 解析，不是按 md 文件位置（脚本已用 `cwd=workdir` 规避）。
- 整页截图型内嵌图（如 p1_img1 全页渲染）与 OCR 内容重复，应跳过不嵌入。
- 公式多时 OCR 建议 `max_tokens=8000`，避免截断。

## 辅助工具：vision_qwen.py（Qwen3-VL 识图）

```bash
python vision_qwen.py ocr <img.png|url> [更多...]        # 单图/多图 OCR 到 stdout
python vision_qwen.py ocr_pdf <input.pdf> --outdir ocr  # PDF 逐页 OCR 到 ocr/pageN.md
python vision_qwen.py extract <input.pdf> --outdir imgs # 提取 PDF 内嵌图片
python vision_qwen.py classify <img...> --out r.txt     # 图片分类(内容图/装饰图/整页截图)
python vision_qwen.py paste [--max 5] [--ocr] [--db x]  # 提取聊天粘贴图片(opencode part表)，--ocr 附带识别
```

- `paste`：从 opencode SQLite 的 `part` 表提取最近粘贴的图片（i 越小越新，默认按 MD5 去重），默认输出到 `%TEMP%\opencode\paste\`（**仅 opencode 环境适用**；其他工具请直接提供图片本地路径）。
- `ocr_pdf` 可接 `--dpi 150`、`--prompt`（默认数学讲义模板 MATH_PROMPT）。

API：SiliconFlow（`https://api.siliconflow.cn/v1`），模型 `Qwen/Qwen3-VL-32B-Instruct`。
Key 优先级：环境变量 `SILICONFLOW_API_KEY` → 脚本内置默认值（失效时更新 `vision_qwen.py` 顶部）。

## 环境要求

- Python 3.8+；`pip install openai PyMuPDF python-docx pillow`
- pandoc 命令行可用（`pandoc --version`）
- 模板：路线A 需 `*.dotx`/`*模板*.docx` 位于工作目录；路线B 默认用本目录 `ref_math_model.docx`（由国赛 `数学建模论文.dotx` 改写，页边距 2.54/2.54/3.17/3.17cm，Normal=Times New Roman 12pt JUSTIFY，Heading1=15pt CENTER）
- Windows 中文控制台需 UTF-8（脚本已内置 `sys.stdout.reconfigure`）
