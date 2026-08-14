---
name: tex-pdf-image-to-word
description: 当用户要求把 LaTeX(.tex) 源码、学术 PDF（含公式与图像）或图片（png/jpg，含聊天粘贴图片）转换成 Word(.docx) 时触发；要求文档包含 OMML 可编辑数学公式、嵌入图片、用预设模板排版（如 NIPT/math 类论文或讲义）时触发。覆盖两条路线：A) tex→docx 直接转换；B) 纯图片 PDF/图片→Qwen OCR→docx 重建。交付前必须过 11 条实测检查清单（正文样式/单倍行距段前段后0/自动编号/符号说明三栏表/OMML 统一/表格不缩进/参考文献/另起一页/要点与代码缩进）。
---

# tex / PDF / 图片 转 Word Skill（OMML 公式 + 图片嵌入）

## 触发条件（任一即触发）
- 用户提供 `.tex` 源码，要求转为 Word（公式必须可编辑 OMML、图片嵌入、套用参考模板）
- 用户提供"只有图片"的 PDF（无文本层，如课件截图/扫描件/手写讲义），要求转成 Word
- 用户提供多张图片或粘贴截图/扫描件，要求合成一个 Word 文档
- 用户说"tex转docx""PDF转word""图片转word""数学公式docx"

## 前置条件（脚本自包含，位于本 SKILL.md 同目录）
- `scripts\tex_to_docx.py` — 路线 A 入口（tex→docx）
- `scripts\preprocess.py` / `scripts\postprocess.py` — tex 预处理/后处理（被 tex_to_docx 调用）
- `scripts\pdf_image_to_docx.py` — 路线 B 入口（纯图 PDF/图片→docx，6 步流水线，含 verify_docx）
- `scripts\vision_qwen.py` — Qwen3-VL-32B OCR 工具（subcommand: ocr / ocr_pdf / extract / classify）
- `scripts\README.md` — 脚本库说明（脚本自包含于本目录）
- `qa\` — docx 质检/编号检查/渲染核对脚本（见「QA 质检脚本速查」；个人路径示例已泛化）
- `assets\ref_math_model.docx` — pandoc 参考模板（自带三线表/公式/图片排版样式）
- 系统依赖：`pandoc`、Python 包 `openai`、`PyMuPDF(fitz)`、`PIL`、`python-docx`
- 视觉模型：SiliconFlow `Qwen/Qwen3-VL-32B-Instruct`（`https://api.siliconflow.cn/v1`）；key 通过环境变量 `SILICONFLOW_API_KEY` 提供（在 https://cloud.siliconflow.cn/me/models 开通），未设置时报错提示；也可用本地 `qwen-mm-plugins` 视觉插件平替或自接其他视觉模型（改 `vision_qwen.py` 的 BASE_URL/MODEL）
- 转换好的 docx 验证与 Word→PDF 渲染预览见脚本 `pdf_image_to_docx.py` 的 `verify_docx` 部分

## QA 质检脚本速查（qa\，全部 UTF-8 安全）
| 脚本 | 用途 |
|------|------|
| `check_docx.py` | 总检：段落数 / 表格数 / OMML 公式数 |
| `check3.py` / `check_content.py` / `check_content2.py` | docx 内容与样式抽查（关键词段、标题样式、对齐） |
| `check_footer.py` | 页脚 PAGE 域与居中检查 |
| `verify_stage1.py` / `verify_stage2.py` | 标题样式+编号+分页检查；列表项 numPr / Body Text 残留检查 |
| `numcheck.py` ~ `numcheck5.py` | 标题编号体系深度检查（numPr / numId↔abstractNum 映射 / 多级列表格式） |
| `tmpl_check.py` | 打印参考模板的标题/正文样式基准 |
| `math_check.py` | 全文裸希腊字母/数学符号文本泄漏检查（非公式内） |
| `extract_images.py` | PDF 内嵌图提取（PyMuPDF） |
| `render_check.py` | PDF 逐页渲染 PNG 预览 |
| `pdf_verify.py` / `pdf_verify2.py` | 各页首行（分页/标题位置）、关键词上下文与公式编号定位 |
| `text_verify.py` | PDF 文本层与 docx 对照 |
| `compare_pages.py` | 源 PDF 与 Word 渲染 PDF 的页面级图片对比 |
| `debug_sec.py` | 章节结构遍历打印 |

## 路线判别
| 输入                       | 走哪条路                                                                 |
|----------------------------|--------------------------------------------------------------------------|
| .tex 源码                  | A：`python tex_to_docx.py in.tex [ref.docx] [out.docx]` |
| PDF 有文本层（可选中复制） | 说明：有文本层直接复制→Word 即可；若用户强调"保留公式/图片"可用 A 的 tex 源，或按 B |
| PDF 无文本层（截图/扫描）  | B：`python pdf_image_to_docx.py in.pdf [--no-ocr]`                        |
| 图片 png/jpg（多张）       | B：先建工作区，按"图片→OCR"处理（见下）                                 |

## 路线 A：tex → docx（公式 OMML、可编辑）
1. 确认输入 tex 在独立工作目录（LaTeX 附图相对路径才会解析成功）
2. 运行（注意是**位置参数**，非 `--flag`）：
   ```
   python tex_to_docx.py input.tex [ref_math_model.docx] [输出.docx]
   ```
3. 源 tex 若含中文注释/中文标题，先将 CWD 设到 tex 目录，并将图片相对路径改为绝对路径
4. 验证：解包 docx 检查 OMML 数量、图片内嵌数、无 `$`/`\` 泄漏（见「验证模板」）

### 路线 A 交付检查清单（用户实测 11 条，缺一不可）
生成后**必须逐项核对**，不满足则写修复脚本（scripts/postprocess.py 已内置大部分修复，见「坑」内的对应编号）：
1. **"正文"样式统一**：pandoc 输出为 `Body Text`/`First Paragraph`（Word 显示"正文文本"），必须把 `w:pStyle` 改为 Normal(`val="1"`)，否则全文没有"正文"样式
2. **单倍行距 + 段前段后 0 磅**：官方模板要求**单倍行距**（不是 1.5 倍！）。正文段落 `w:spacing line=240 lineRule=auto before=0 after=0` + 首行缩进 `w:ind firstLineChars=200`；页边距四边 2.5cm（pandoc 默认 2.54/3.17cm 必须改）
3. **技术路线/流程转录伪影清洗**：OCR/转录出的文本常见圆圈符号（●○◎►◆）与"技术路线为："这类冗余引导句——必须删除引导句，圆圈 bullet 转成正常排版列表或直接删除（用户原话：'技术路线为...这个转录有问题，有好多个圆圈，且这种说法有点怪，没必要有'）
4. **标题序号只留自动标号**：标题文字删掉"1 "、"1.1 "等序号前缀，只用 `w:numPr`(numId 引用 numbering.xml 多级列表, ilvl=0/1/2) 自动编号；复用 ref 模板的 numbering（含 %1.%2.%3 abstractNum）；附录/代码标题**不**加编号（文本以"附录"/"代码："开头则跳过）
5. **符号说明三栏表**：符号说明必须为"符号 | 符号说明 | 单位"三栏表（用户原话：'符号说明要用正文范式，符号 符号说明 单位'）；表内段落无缩进、五号字
6. **数学符号统一 OMML**：公式必须全部 OMML；正文/表格/题注中不得有 `$`、`\`、Unicode 数学符号（α/±/×/∑等）零星文本出现（pandoc 正常时不会，OCR 路线的清洗见路线 B 步骤 6）
7. **正文缩进、表格不缩进**：正文首行缩进 2 字符，但**表格单元格内段落必须显式 `w:ind firstLine=0 firstLineChars=0`**
8. **参考文献整理**：编号连续、格式统一（书/刊/网三格式，见 official-paper-format.md 十四）、正文有 [编号] 标注、无乱序（用户原话：'参考文献是乱的'）
9. **另起一页**：附录标题与参考文献标题必须另起一页（`w:pageBreakBefore` 或分页符，postprocess.py 已内置）；全文格式不乱（用户原话：'附录的标题还有参考文献的标题要另起一页，这些格式都乱了'）
10. **要点缩进统一**：列表/要点段落统一挂起缩进（`w:ind left=360 hanging=360`），不美观的缩进必须修复
11. **附录代码缩进**：附录代码段落用等宽字体、不首行缩进（`w:ind firstLineChars=0`），保持代码原始缩进层级

## 路线 B：纯图片 PDF / 图片 → docx（OCR 重建）
`pdf_image_to_docx.py` 六步：
1. 渲染：PyMuPDF 每页 → `{ocr_dir}/_pages/pageN.png`（dpi 可调，默认 150）
2. OCR：每页送 Qwen3-VL-32B，按 `ocr/pageN.md` 落盘（数学公式给 LaTeX；页面内嵌图占位写 `[图N]`）；可用 `--no-ocr` 跳过（已有 ocr/*.md 时）
3. 提取图片：PDF 内嵌图 → `{workdir}/imgs/p{pno}_img{n}.png`
4. 建图映射：支持
   - 自动：`auto_map_imgs` 按页内 `[图N]` 占位顺序匹配，宽度按像素 96dpi 换算(≤13cm 上限)
   - 手工：`--img-map '(1,1):["p1_img1.png","9cm"]; (2,3):["p2_img3.png","12cm"]'`（**注意引号内不能有空格**，PowerShell 传参需转义）
5. 组装+转换：合并所有 page*.md → `combined.md`，pandoc(`-f markdown -t docx --reference-doc ref`) → docx（pandoc 的 CWD 已自动设为 workdir，图片相对路径才解析成功）
6. **数学公式清洗（必经步骤，防 LaTeX 泄漏）**：OCR 输出 `$...$` 中 `$` 前若有多余空格（如 `= $（ `），pandoc 的 `tex_math_dollars` 不识别会成为普通文本 `$`。修复：把 `${...}` 前空格去掉：
   ```python
   md = re.sub(r'[ \t]+\$', '$', md)   # 只删 $ 前空格，保留 $ 配对
   # 不要用 r'\$([^$\n]*?)\s+\$' —— 会吞掉前一公式的开头 $ 破坏配对
   ```
6b. **转录伪影清洗**：OCR 常把流程图/技术路线转录成一串圆圈符号（●○◎►◆▪）和"技术路线为："这类冗余引导句。修复：删除引导句；圆圈 bullet 转正常列表或直接删除；成对圆圈夹文字（如 ○xxx○）按嵌套列表重建。这条与路线 A 检查清单第 3 条同源。
7. 验证：`verify_docx` 输出 段落/表格/图片/OMML 计数 + Word→PDF 渲染

### 图片场景（用户给图片而非 PDF）
```
建一个临时工作目录 T；把图片按页序命名 page1.png, page2.png...
python vision_qwen.py ocr T/page1.png --out T/ocr/page1.md ... 逐页
按路线 B 第 4 步以可手动映射 --img-map 指定每页图片
```

## OCR 子命令速查（vision_qwen.py）
- `ocr <img>` — 单图 OCR 到 stdout 或 `--out file`
- `ocr_pdf <pdf> --dpi 150` — 整份 PDF 逐页 → 每页 md >`ocr_dir/pageN.md`（内含数学 LaTeX + `[图N]` 占位）
- `extract <pdf> --out imgs` — 把 PDF 内嵌图提取为 `p{p}_{n}.png`
- `classify <img...>` — 判断图片是"整页截图/内容图/装饰图"，供建图映射参考

## 验证模板（docx 质检）
解包检查（脚本已内置，也可手动）：
```python
import zipfile, re
xml = zipfile.ZipFile(out.docx).read("word/document.xml").decode("utf-8")
print(re.findall(r"<w:p[ >]", xml).__len__(), "段落")
print(xml.count("<w:drawing>"), "图片")
print(xml.count("<m:oMath"), "OMML公式")
assert "$" not in re.sub(r"<[^>]+>", "", xml)  # 防止 LaTeX 泄漏
```
- 期望数值：图片 = IMG_MAP 应用到的 `[图N]` 个数；公式全为 OMML，无 `$`/`\` 残留
- 步骤 6 的清洗必须跑（OCR 输出经常出现 `= $` bug）

## 坑（已实测踩过，务必避免）
1. **`pandoc` 相对图片路径按进程 CWD 解析，而非按 md 文件位置**——脚本用 `subprocess.run(..., cwd=workdir)` 解决；手写调用务必加 `cwd` 指向 md 所在目录
2. **`$(...)` OCR 泄漏**：OCR 文案 `= $（` 中 `$` 前出现空格 → 修复为 `=$\left(...)` 前删除空格；pandoc 才识别为数学模式
3. **`--img-map` 传参格式**：`'(1,1):["p1_img1.png","9cm"]'`，键为 `(页码,图号)`，值为 `(文件名,宽度cm)` 元组。PowerShell 下中文路径/硬引号转义易错，复杂场景在脚本内改 `IMG_MAP` 常量或改用 JSON 文件传参
4. **PowerShell → Python argv 中文乱码**：Windows PowerShell 5.1 传 中文 路径参数会乱码。规避：把路径写死在脚本内（如 run_*.py 内部用字面量）执行，或用 `--config` JSON 传参，或改用 Git Bash
5. **OMML 可行性**：pandoc `tex_math_dollars` 已接受 `$...$`，但 `\dfrac` 宏部分引擎不支持，公式务必写纯 LaTeX 数学可识别（`\dfrac`等需 preprocess 步骤预清洗为可读等价形式）
6. **`sys.stdout` 编码**：脚本必须 `.reconfigure(encoding="utf-8")`，否则输出中文/公式触发 GBK 报错（所有脚本已内置）
7. **视觉模型 OCR 慢**：单图 1–2 分钟，多页给足超时（300s），批量用并发脚本文件内循环（不要 12 个图一次跑进 bash 超时）
8. **图片宽度**：auto_map 按像素/96dpi=cass，可手工微调 `--img-map` 设 cm 值；内容图默认 9–12cm
9. **subfigure 并排图被 pandoc 转成表格**：tex 中 `\begin{subfigure}` 两张图并排时，pandoc 输出为 1 行 2 列表格（图为 `<w:drawing>` 在 `w:tbl > w:tr > w:tc` 内），用户会反馈"图片没正常插入"。
   修复：遍历 body 找含 `w:drawing` 的表格，把每个 tc 内的段落（图段+子图题段）`addprevious` 到表格前，再 `remove` 表格——图恢复为普通正文段落
10. **多行 `\ctexset{...}` 残留 `}` 导致 pandoc 崩**：preprocess 按行匹配 `^\ctexset` 删除首行，但多行写法的收尾 `}` 行残留 → pandoc 报 `unexpected Tok "}"`。修复：删掉文件中孤立闭合 `}` 行；或 preprocess 按花括号配对删除整块
11. **postprocess 遇空表（0 行）IndexError 崩**：`tbl.rows[0]` 对空表抛 `list index out of range`。修复：循环开头加 `if not tbl.rows: continue`
12. **postprocess 重复跑 ⇒ 公式编号叠加**：如 `(5.1)(5.1)` 双编号。同一 docx 只允许后处理一次；重跑流水线要回到 pandoc 步骤重新生成，不要在已有后处理产物的 docx 上再跑
13. **PyMuPDF 提取 PDF 文本误报乱码 ≠ 渲染错误**：验证 docx 渲染效果时，用 `pdf_to_png` 渲染页面 PNG 再调 `vision_qwen.py ocr` 看真实显示（模型不支持图片输入时此法必用），不要只看 fitz `get_text()`（OMML 公式文本层提取常乱码，但渲染正常）

## 验证与交付
- 转换成功后询问用户：(a) 是否需要 Word 打开确认；(b) 是否同时导出 PDF（Win32 COM `SaveAs2(...,FileFormat=17)`，退出 COM 会报无意的 COMException——忽略，是退出的常见伪报）
- 交付 docx 到用户指定路径，同时提示"公式已 OMML 可编辑、图片已内嵌"