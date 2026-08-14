---
name: vision-ocr
description: 当用户发送、附加或提到 PDF/图片文件（png/jpg/jpeg/bmp/webp）并要求识图、OCR、读取论文内容、提取图表数据、识别截图/文档时触发。用 SiliconFlow 的 Qwen3-VL 视觉模型（8B 默认提速 + 32B 关键页复核）识别图片或 PDF 页面。含上下文预算约束（OCR 结果落盘文件、禁止整本进对话，防 1M token 爆掉）。也被 competition-workflow（读题）、guozhan-paper（读范文）、tex-pdf-image-to-word（路线B）调用。
---

# 视觉识图 Skill：Qwen3-VL-32B OCR

## 触发条件（出现任一即触发）
- 用户附加或提供图片路径（.png/.jpg/.jpeg/.bmp/.webp）
- 用户粘贴图片到聊天窗口（当前模型不支持图片输入，报 "Cannot read image.png" 时，说明是粘贴附件）
- 用户附加或提供 PDF 文件路径，要求"读一下/看一下/验证/提取内容"
- 用户说"识图""OCR""看这张图""读这个PDF""识别图表/截图/文档"

## 调用方（谁在什么阶段调我）

| 调用方 | 场景 | 用法 |
|--------|------|------|
| competition-workflow | 阶段 0 读题：OCR 题面 PDF/附件图 | 关键页优先，落盘后按需取段 |
| guozhan-paper | 读国奖论文 PDF 提炼写作范式 | 同上，逐页落盘 |
| tex-pdf-image-to-word | 路线 B：纯图 PDF/图片 → docx 重建 | 逐页 OCR 落盘 ocr/pageN.md（含 LaTeX 公式 + [图N] 占位） |
| 用户直接请求 | 识图/读 PDF/提取图表数据 | 按下方工作流 |

## 核心原则
- **图片/PDF 内容必须交给 Qwen3-VL 视觉模型识别**，不要只用文本提取（PDF 文本层缺公式/图表/表格布局信息；图片则必须走视觉模型）
- 双档模型：**8B 默认提速，32B 关键页复核**（表格数字/公式/流程图节点页），规则见「执行策略·提速」
- PDF 处理：先用 PyMuPDF（fitz）把每页渲染成 PNG（dpi≈150），再送视觉模型
- 视觉模型输出会进入对话上下文，供后续分析直接使用

## 工作流

### 1. 输入判别
- 扩展名 `.pdf` → 渲染为 PNG（临时目录，如 `%TEMP%` 下自建子目录）
- 本地图片路径 → 直接调用
- **聊天粘贴图片（无本地路径）** → 环境自适应：opencode 下从 SQLite 落盘，其他工具请用户提供本地路径（见下方「粘贴图片提取」章节）
- 支持多张/多页批量，一次调用可传多图

### 0. 粘贴图片提取（聊天附件落盘）

**环境自适应（本节仅 opencode 需要）**：先判断——若当前工具不是 opencode，或不存在 `%USERPROFILE%\.local\share\opencode\opencode.db`（Linux 为 `~/.local/share/opencode/opencode.db`），则跳过本节，直接请用户提供图片本地路径后按普通图片流程走 `ocr_image()`。

opencode 会把用户粘贴的图片以 base64 形式存进 `part` 表（`type: file`, `mime: image/*`）。用脚本提取最新一张到临时目录：

```python
# -*- coding: utf-8 -*-
import sqlite3, json, base64

DB = r"%USERPROFILE%\.local\share\opencode\opencode.db"  # Windows；Linux 为 ~/.local/share/opencode/opencode.db
OUT = os.path.join(tempfile.gettempdir(), "opencode")  # 可改为任意临时目录

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT id, session_id, data FROM part WHERE data LIKE '%data:image%' ORDER BY time_created DESC"
).fetchall()
for i, r in enumerate(rows):
    d = json.loads(r["data"])
    if d.get("type") == "file" and d.get("mime", "").startswith("image/"):
        b64 = d["url"].split(",", 1)[1]
        raw = base64.b64decode(b64)
        ext = d["mime"].split("/")[-1].replace("jpeg", "jpg")
        path = rf"{OUT}\pasted_{i}.{ext}"
        with open(path, "wb") as f:
            f.write(raw)
        print(f"{path} | {len(raw)} bytes | {d.get('filename')}")
conn.close()
```

- **i 越小越新**（按 time_created DESC 排序，i=0 是最近一次粘贴）
- 优先提取 `i=0` 或与最近时间戳匹配的图片；旧图（如之前重复粘贴的）跳过或留给用户确认
- 提取后按普通图片路径流程走 `ocr_image()`

### 2. 调用视觉模型
API：`https://api.siliconflow.cn/v1`（OpenAI 兼容），模型 `Qwen/Qwen3-VL-32B-Instruct`，消息格式：

```
content: [
  {"type": "text", "text": OCR_PROMPT},
  {"type": "image_url", "image_url": {"url": <图片URL 或 data:image/png;base64,...>}}
]
```

OCR_PROMPT 模板：
```
你是一个专业的 OCR 引擎。请精确提取图片中的全部内容：
- 文字：逐字转录，保留原始排版（段落、换行、缩进）
- 表格：输出为 Markdown 表格，保留所有数值与表头
- 图表：提取标题、坐标轴、图例、关键数据点（用表格或 JSON）
- 数学公式：用 LaTeX 或可读符号表示（如 σ²_u、Ŷ、B_j）
- 若图片无文字，简要描述图片内容
只输出提取结果本身，不要添加任何解释。
```

### 3. 可复用代码模板（已含全部坑的处理）

```python
# -*- coding: utf-8 -*-
import os, sys, re, base64, mimetypes, tempfile
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from openai import OpenAI

API_KEY = os.environ.get("SILICONFLOW_API_KEY")  # 必填：到 https://cloud.siliconflow.cn/me/models 开通视觉模型（推荐 Qwen3-VL-8B/32B-Instruct）后，把 key 设为环境变量 SILICONFLOW_API_KEY；未设置时脚本应报错提示，禁止硬编码
MODEL = "Qwen/Qwen3-VL-32B-Instruct"
BASE_URL = "https://api.siliconflow.cn/v1"
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

OCR_PROMPT = "你是一个专业的 OCR 引擎。请精确提取图片中的全部内容：文字逐字转录保留排版；表格输出为 Markdown 表格保留全部数值；图表提取标题/坐标轴/图例/数据点；数学公式用 LaTeX 或可读符号；无文字则简要描述。只输出提取结果本身。"

def encode_image(path):
    mime, _ = mimetypes.guess_type(path)
    with open(path, "rb") as f:
        return f"data:{mime or 'image/png'};base64,{base64.b64encode(f.read()).decode()}"

def ocr_image(src, max_tokens=4096, temperature=0.1):
    if src.lower().startswith(("http://", "https://", "data:")):
        url = src
    else:
        url = encode_image(src)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": OCR_PROMPT},
            {"type": "image_url", "image_url": {"url": url}}]}],
        temperature=temperature, max_tokens=max_tokens)
    return resp.choices[0].message.content

def pdf_to_images(pdf_path, dpi=150, outdir=None):
    import fitz  # PyMuPDF
    outdir = outdir or os.path.join(tempfile.gettempdir(), "vision-ocr", "pages")
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf_path)
    paths = []
    for i, page in enumerate(doc):
        p = os.path.join(outdir, f"{os.path.splitext(os.path.basename(pdf_path))[0]}_p{i+1:02d}.png")
        page.get_pixmap(dpi=dpi).save(p)
        paths.append(p)
    return paths  # 返回页码序列表
```

### 4. 执行策略（含上下文预算约束）

**上下文预算铁律（codex 实测 1M token 上限）**：OCR 文本是上下文最大杀手——66 页 PDF 全量拼接可直接爆掉 1M token（报错 `maximum context length is 1048576 tokens`）。必须遵守：
- **OCR 结果一律落盘文件**（如 `ocr/pageNN.md`），**禁止整本进对话**；对话里只放 ≤500 字的摘要与关键数字。
- **单次模型调用只送 1 页**（最多 2 页）图片，逐页串行识别；每页结果单独成一个文件。
- **需要哪段读哪段**：用 grep/offset 定向取段，绝不整本 read。
- **大 PDF（>8 页）先只识别关键页**：摘要页/目录页/结果表页；其余页按需再识别。
- **一旦触发 context length 报错**：立即停止全量识别，清掉对话中已拼入的原始 OCR 文本，改为"逐页落盘 + 定向取段"模式。
- 单张图片/少量页面：直接 `ocr_image()`，结果写文件、摘要进对话。
- 每页调用超时按 120–300s；识别结果较长时写临时 txt 后定向读取（防输出截断，也防上下文膨胀）。

**提速规则（DSH 实测：并发 4 线程 + 8B 默认，84 页约 12 分钟；32B 串行同量约 70 分钟，提速约 6 倍）**：
- 批量页用 `ThreadPoolExecutor`（4 并发）+ 8B 模型（`Qwen/Qwen3-VL-8B-Instruct`），每页落盘；**文件名或文件头标注模型**（如 `# 第N页（Qwen3-VL-8B）`）。
- **8B 页面的数字类结论一律降置信度标注**；表格数字、流程图节点、公式密集页 → 用 32B 单页复核（复核前删除旧文件强制重扫）。
- **断点续传**：输出文件已存在且非空即跳过，中断可重入。
- **失败降级**：32B 失败 → 8B 兜底重试；8B 失败 → 退避重试 3 次。
- 实战模板：`../../assets/ocr_batch.py`（并发+双档+降级+续传的通用版，可直接复制改造）。

## 注意事项（踩过的坑）
1. **Windows 编码**：脚本必须 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`，否则模型返回的 ²、σ、下标等字符会触发 GBK 编码异常
2. **本地图片**：必须转 base64 data URL（`data:image/png;base64,...`），直接传本地路径无效
3. **速度实测**：8B 约 15-25s/页，32B 约 50-90s/页（并发 4 时吞吐更高）；超时时间给足（≥300s）
4. **账户**：SiliconFlow 余额不足时返回 402/30001，需提示用户充值
5. **PDF 文本层**：PyMuPDF 提取的文本可用于快速预览/数字对比，但表格布局、公式、图片内文字必须走视觉模型
6. **识别准确性**：验证数字时以视觉模型输出+代码复算双通道交叉核对
7. **聊天粘贴图片**：仅在 opencode 下会落盘到其 SQLite（`part` 表），用「粘贴图片提取」脚本落盘再识别；其他工具不提供该落盘机制，需请用户给出图片本地路径，再走视觉模型
8. **同图多次粘贴**：数据库会保留多条相同记录，提取时对比文件大小/字节数去重，避免重复识别

## 输出到上下文的格式（预算版）
```
===== <文件名>：共 N 页，已识别关键页 M 页 =====
- 完整文本已落盘：<目录>/pageNN.md
- 摘要：<每页 1-2 句，全文 ≤500 字>
- 关键数字/表格：<用户关心的数值>
===== 需要哪页详情请指定页码 =====
```
**只输出摘要与文件路径，不输出整本 OCR 文本**。识别完成后，主动说明关键内容摘要，供用户继续提问分析；用户要细节时再定向读取对应页文件。
