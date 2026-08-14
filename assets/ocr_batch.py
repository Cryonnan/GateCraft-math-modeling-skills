# -*- coding: utf-8 -*-
"""通用批量 OCR：并发 4 线程 + 8B/32B 双档模型 + 断点续传 + 失败降级。

用法:
  python ocr_batch.py <页图目录> <输出目录> <页码列表...>
  # 页码前加 B 表示用 32B 大模型（表格数字/流程图/公式密集页），其余默认 8B
  python ocr_batch.py pages/ ocr/ 1 2 3 B4 5

环境变量:
  SILICONFLOW_API_KEY  必填，在 https://cloud.siliconflow.cn/me/models 开通
                       视觉模型后获取（推荐 Qwen3-VL-8B-Instruct / 32B-Instruct）
页图文件命名: <前缀>_NNN.<ext>（前缀与扩展名自动探测，取目录中数量最多的一种）
输出: <输出目录>/pageNNN.md，文件头标注所用模型；已存在且非空的页自动跳过（断点续传）
"""
import sys, os, base64, time
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from openai import OpenAI

API_KEY = os.environ.get("SILICONFLOW_API_KEY")
if not API_KEY:
    sys.exit("错误：未设置 SILICONFLOW_API_KEY 环境变量。"
             "请到 https://cloud.siliconflow.cn/me/models 开通视觉模型后设置。")

BASE = "https://api.siliconflow.cn/v1"
MODEL_FAST = "Qwen/Qwen3-VL-8B-Instruct"
MODEL_BIG = "Qwen/Qwen3-VL-32B-Instruct"

PROMPT = """你是一个专业的论文页面 OCR 引擎。请精确提取这页图片的全部内容：
- 文字逐字转录，保留段落与编号
- 表格输出为 Markdown 表格，保留全部数值与表头
- 图表：给出图号/表号与标题；若是流程图，请逐步描述节点与箭头文字
- 数学公式用 LaTeX 或可读符号
只输出提取结果本身，不要添加解释。"""


def find_page_files(pages_dir):
    """自动探测页图命名：返回 {页号: 文件路径}"""
    import re
    mapping = {}
    for name in os.listdir(pages_dir):
        m = re.search(r"_(\d{3})\.(png|jpg|jpeg|webp|bmp)$", name)
        if m:
            mapping[int(m.group(1))] = os.path.join(pages_dir, name)
    return mapping


def ocr_one(n, img, out_dir, big_model=False, retry=2):
    out = os.path.join(out_dir, f"page{n:03d}.md")
    if os.path.exists(out) and os.path.getsize(out) > 200:
        return f"p{n} skip(exists)"
    with open(img, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    for attempt in range(retry + 1):
        model = MODEL_BIG if big_model else MODEL_FAST
        try:
            client = OpenAI(api_key=API_KEY, base_url=BASE)
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
                temperature=0.1, max_tokens=3072)
            txt = resp.choices[0].message.content
            with open(out, "w", encoding="utf-8") as f:
                f.write(f"# 第{n}页（{model}）\n\n{txt}")
            return f"p{n} OK({model.split('/')[-1][:7]})"
        except Exception as e:
            if attempt == retry:
                if big_model:
                    try:
                        client = OpenAI(api_key=API_KEY, base_url=BASE)
                        resp = client.chat.completions.create(
                            model=MODEL_FAST,
                            messages=[{"role": "user", "content": [
                                {"type": "text", "text": PROMPT},
                                {"type": "image_url",
                                 "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
                            temperature=0.1, max_tokens=3072)
                        txt = resp.choices[0].message.content
                        with open(out, "w", encoding="utf-8") as f:
                            f.write(f"# 第{n}页（降级 {MODEL_FAST}）\n\n{txt}")
                        return f"p{n} OK(fallback)"
                    except Exception as e2:
                        return f"p{n} FAIL: {str(e2)[:100]}"
                return f"p{n} FAIL: {str(e)[:120]}"
            time.sleep(3 * (attempt + 1))
    return f"p{n} FAIL"


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return
    pages_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    args = sys.argv[3:]
    big_pages, pages = set(), []
    for a in args:
        if a.startswith("B"):
            big_pages.add(int(a[1:]))
        else:
            pages.append(int(a))
    files = find_page_files(pages_dir)
    print(f"页图目录 {pages_dir}: 探测到 {len(files)} 页；待识别 {len(pages)} 页（32B: {sorted(big_pages)}），并发 4", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {}
        for p in pages:
            if p in files:
                futs[ex.submit(ocr_one, p, files[p], out_dir, p in big_pages)] = p
            else:
                print(f"p{p} 无对应页图，跳过", flush=True)
        done = 0
        for fu in as_completed(futs):
            done += 1
            print(f"[{done}/{len(futs)}] {fu.result()}  (+{time.time()-t0:.0f}s)", flush=True)
    print(f"完成，用时 {time.time()-t0:.0f}s；结果落盘 {out_dir}")


if __name__ == "__main__":
    main()
