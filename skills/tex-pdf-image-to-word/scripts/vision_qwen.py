# -*- coding: utf-8 -*-
"""
Qwen3-VL 视觉识图系统化工具（从 Vision-OCR skill 抽取）

功能:
    - 单图/多图 OCR（返回文本）
    - PDF 渲染为 PNG
    - PDF 逐页 OCR 到 Markdown（自动保存到目录）
    - PDF 内嵌图片提取（按页命名 p{i}_img{j}.png）
    - 图片分类（内容图 / 装饰图）

用法：
    python vision_qwen.py ocr <图片或url> [更多图片...]
    python vision_qwen.py ocr-pdf <input.pdf> [--outdir <dir>] [--dpi 150]
    python vision_qwen.py extract <input.pdf> [--outdir <dir>]
    python vision_qwen.py classify <img1> [img2...] [--out <txt>]

依赖：openai, PyMuPDF(fitz)；Windows 中文需 Python 3.7+ 支持 sys.stdout.reconfigure
"""

import os, sys, re, base64, mimetypes, tempfile, argparse

if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from openai import OpenAI

API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
MODEL = "Qwen/Qwen3-VL-32B-Instruct"
BASE_URL = "https://api.siliconflow.cn/v1"


def get_client():
    """从环境变量 SILICONFLOW_API_KEY 读取；未设置时报错提示（key 申请见 https://cloud.siliconflow.cn/me/models）"""
    if not API_KEY:
        raise RuntimeError(
            "未设置 SILICONFLOW_API_KEY 环境变量。请到 https://cloud.siliconflow.cn/me/models "
            "开通 Qwen3-VL 视觉模型后设置该环境变量。")
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


CLIENT = get_client()

OCR_PROMPT = (
    "你是一个专业的 OCR 引擎。请精确提取图片中的全部内容："
    "文字逐字转录保留排版；表格输出为 Markdown 表格保留全部数值；"
    "图表提取标题/坐标轴/图例/数据点；数学公式用 LaTeX 完整表示；"
    "无文字则简要描述。只输出提取结果本身。"
)

# 数学讲义专用：公式 LaTeX + 图片占位符 [图N]
MATH_PROMPT = """你是高中数学/数模讲义的 OCR 引擎。这是课件截图，请精确转录为 Markdown：
1. 标题层级用 # / ## / ###
2. 正文、例题、解析、选择题逐字转录，保留题号与选项 A/B/C/D
3. 数学公式用 LaTeX：行内公式 $...$，独立公式 $$...$$（上下标、分式、根号、求和符号要完整）
4. 保留公式编号 (1)、(2)
5. 图片/图形出现的位置输出占位符 [图N]，N 从 1 开始按页内出现顺序编号，并括号简述图形内容（如 [图1]（坐标系中的二次函数图像））
6. 表格用 Markdown 表格
只输出 Markdown 内容本身，不要添加任何解释。"""

# 图片类型判断（用于 PDF 重建 Word 时决定哪些图是教学内容）
CLASSIFY_PROMPT = """判断这张图片的类型，只回答其一：
A. 内容图（函数图像/坐标系/几何图形/曲线图等教学内容）
B. 装饰图（分隔线/背景/水印/边框等）
C. 整页截图（整页内容渲染图，与文字 OCR 重复）
并一句话说明图像内容。"""


def encode_image(path):
    mime, _ = mimetypes.guess_type(path)
    with open(path, "rb") as f:
        return f"data:{mime or 'image/png'};base64,{base64.b64encode(f.read()).decode()}"


def ocr_image(src, prompt=OCR_PROMPT, max_tokens=4096, temperature=0.1,
              image_size=None):
    """识别单张图片；src 可为本地路径/URL/dataURI。返回文本。"""
    if isinstance(src, (list, tuple)):
        return ocr_multi(list(src), prompt=prompt, max_tokens=max_tokens,
                         temperature=temperature)
    if src.lower().startswith(("http://", "https://", "data:")):
        url = src
    else:
        url = encode_image(src)
    msg = [{"type": "text", "text": prompt},
           {"type": "image_url", "image_url": {"url": url}}]
    resp = CLIENT.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": msg}],
        temperature=temperature, max_tokens=max_tokens)
    return resp.choices[0].message.content


def ocr_multi(srcs, prompt=OCR_PROMPT, max_tokens=4096, temperature=0.1):
    """一次请求识别多张图（部分模型不支持多图，失败时回退逐张）"""
    content = [{"type": "text", "text": prompt}]
    for s in srcs:
        url = s if s.lower().startswith(("http://", "https://", "data:")) else encode_image(s)
        content.append({"type": "image_url", "image_url": {"url": url}})
    try:
        resp = CLIENT.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": content}],
            temperature=temperature, max_tokens=max_tokens)
        return resp.choices[0].message.content
    except Exception:
        return "\n\n".join(ocr_image(s, prompt=prompt, max_tokens=max_tokens,
                                     temperature=temperature) for s in srcs)


def pdf_to_images(pdf_path, dpi=150, out_dir=None):
    """PDF 每页渲染 PNG。返回按页序的路径列表。"""
    import fitz
    out_dir = out_dir or os.path.join(tempfile.gettempdir(), "opencode", "pages")
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    paths = []
    for i, page in enumerate(doc):
        p = os.path.join(out_dir,
                         f"{os.path.splitext(os.path.basename(pdf_path))[0]}_p{i+1:02d}.png")
        page.get_pixmap(dpi=dpi).save(p)
        paths.append(p)
    return paths


def ocr_pdf_to_md(pdf_path, prompt=MATH_PROMPT, dpi=150, out_dir=None,
                  max_tokens=8000, page_pattern="page{}.md"):
    """渲染+逐页 OCR 到 Markdown 文件。返回 (页面渲染列表, 输出md列表)。"""
    import fitz
    out_dir = out_dir or os.path.join(os.path.dirname(pdf_path) or ".", "ocr")
    os.makedirs(out_dir, exist_ok=True)
    imgs = pdf_to_images(pdf_path, dpi=dpi, out_dir=os.path.join(out_dir, "_pages"))
    mds = []
    for i, p in enumerate(imgs):
        txt = ocr_image(p, prompt=prompt, max_tokens=max_tokens)
        md_path = os.path.join(out_dir, page_pattern.format(i + 1))
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(txt)
        mds.append(md_path)
        print(f"page{i+1} done, {len(txt)} chars -> {md_path}")
    return imgs, mds


def extract_embedded_images(pdf_path, out_dir=None):
    """提取 PDF 内嵌图，命名 p{i}_img{j}.png。返回文件列表。"""
    import fitz
    out_dir = out_dir or os.path.join(os.path.dirname(pdf_path) or ".", "imgs")
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    files = []
    for pno in range(len(doc)):
        for j, img in enumerate(doc[pno].get_images(full=True), 1):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n - pix.alpha >= 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            name = f"p{pno+1}_img{j}.png"
            path = os.path.join(out_dir, name)
            pix.save(path)
            files.append(path)
            print(f"{name}: {pix.width}x{pix.height}")
    return files


def classify_image(path, prompt=CLASSIFY_PROMPT, max_tokens=300):
    return ocr_image(path, prompt=prompt, max_tokens=max_tokens)


def opencode_db_path():
    """定位 opencode SQLite 数据库（Windows 优先）"""
    cands = [
        os.path.join(os.path.expanduser("~"), ".local", "share", "opencode", "opencode.db"),
        os.path.join(os.path.expanduser("~"), ".config", "opencode", "opencode.db"),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return cands[0]


def extract_pasted_images(db=None, out_dir=None, max_count=5, dedup=True):
    """从 opencode part 表提取聊天粘贴的图片到磁盘。返回 [路径, ...]。
    i 越小越新（按 time_created DESC 排序，i=0 是最近一次）。"""
    import sqlite3, json, hashlib
    db = db or opencode_db_path()
    out_dir = out_dir or os.path.join(tempfile.gettempdir(), "opencode", "paste")
    os.makedirs(out_dir, exist_ok=True)
    if not os.path.exists(db):
        print(f"[paste] 未找到数据库: {db}")
        return []
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, data FROM part WHERE data->>'mime' LIKE 'image/%' "
        "ORDER BY time_created DESC").fetchall()
    conn.close()
    seen = set()
    paths = []
    n = 0
    for r in rows:
        import json
        d = json.loads(r["data"]) if isinstance(r["data"], str) else r["data"]
        if not (isinstance(d, dict) and d.get("type") == "file"):
            continue
        url = d.get("url", "")
        if not url.startswith("data:image"):
            continue
        try:
            raw = base64.b64decode(url.split(",", 1)[1])
        except Exception:
            continue
        if dedup:
            h = hashlib.md5(raw).hexdigest()
            if h in seen:
                continue
            seen.add(h)
        ext = {"png": "png", "jpeg": "jpg", "jpg": "jpg", "webp": "webp",
               "bmp": "bmp", "gif": "gif"}.get(
                   (d.get("mime", "") or "").split("/")[-1], "png")
        path = os.path.join(out_dir, f"pasted_{n}.{ext}")
        with open(path, "wb") as f:
            f.write(raw)
        print(f"[paste] {path} | {len(raw)} bytes | {d.get('filename')}")
        paths.append(path)
        n += 1
        if n >= max_count:
            break
    if not paths:
        print("[paste] 未找到粘贴图片")
    return paths


def main():
    ap = argparse.ArgumentParser(prog="vision_qwen",
                                 description="Qwen3-VL 识图/PDF OCR 工具")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("ocr", help="单图/多图 OCR")
    p1.add_argument("inputs", nargs="+")
    p1.add_argument("--prompt", default=OCR_PROMPT)
    p1.add_argument("--max-tokens", type=int, default=4096)

    p2 = sub.add_parser("ocr_pdf", help="PDF 逐页 OCR 到 Markdown")
    p2.add_argument("pdf")
    p2.add_argument("--outdir")
    p2.add_argument("--dpi", type=int, default=150)

    p3 = sub.add_parser("extract", help="提取 PDF 内嵌图片")
    p3.add_argument("pdf")
    p3.add_argument("--outdir")

    p4 = sub.add_parser("classify", help="图片分类（内容图/装饰图/整页截图）")
    p4.add_argument("images", nargs="+")
    p4.add_argument("--out")

    p5 = sub.add_parser("paste", help="提取聊天粘贴的图片(opencode part表)")
    p5.add_argument("--db")
    p5.add_argument("--outdir")
    p5.add_argument("--max", type=int, default=5)
    p5.add_argument("--no-dedup", action="store_true", help="不去重")
    p5.add_argument("--ocr", action="store_true", help="提取后顺便识别")

    args = ap.parse_args()
    if args.cmd == "paste":
        paths = extract_pasted_images(db=args.db, out_dir=args.outdir,
                                      max_count=args.max, dedup=not args.no_dedup)
        if args.ocr and paths:
            for p in paths:
                print("=" * 60)
                print(p)
                print("=" * 60)
                print(ocr_image(p))
    elif args.cmd == "ocr":
        for s in args.inputs:
            print("=" * 60)
            print(s)
            print("=" * 60)
            print(ocr_image(s, prompt=args.prompt, max_tokens=args.max_tokens))
    elif args.cmd == "ocr_pdf":
        imgs, mds = ocr_pdf_to_md(args.pdf, dpi=args.dpi, out_dir=args.outdir)
        print("页面渲染:", imgs)
        print("OCR 输出:", mds)
    elif args.cmd == "extract":
        extract_embedded_images(args.pdf, out_dir=args.outdir)
    elif args.cmd == "classify":
        lines = []
        for im in args.images:
            lines.append(f"===== {im} =====")
            lines.append(classify_image(im))
        res = "\n\n".join(lines)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(res)
            print("已保存到", args.out)
        else:
            print(res)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()