# -*- coding: utf-8 -*-
"""流程图生成器：JSON 规格 → .drawio XML（+ 可选 mermaid 预览）

用法:
  python flowchart_gen.py spec.json
规格 JSON:
  {
    "kind": "stages",              # 每问流程图: 四阶段横向
    "title": "问题二：基于 BMI 分组的 NIPT 时点优化",
    "stageTitles": ["①数据处理","②模型建立","③约束与检验","④求解与敏感性"],
    "stages": [ ["计算达标概率 p(t,b)","最早达标时间 T*(b)"],
                ["目标：加权总风险+分组复杂度惩罚 λK"],
                ["保障率约束","单调性约束"],
                ["动态规划 DP","κ×q 敏感性分析"] ],
    "edgeLabels": [null, null, null],   # 阶段间箭头文字(传递物/顺序说明)，长度=阶段数-1
    "out": "p2_flowchart.drawio"
  }
  或 kind="chain"（总体技术路线图）:
  {
    "kind": "chain",
    "title": "NIPT 时点优化总体技术路线",
    "chain": [
      {"title":"问题一","methods":["logit+LMM","随机截距/斜率"],"pass":"浓度模型 p(t,b)"},
      {"title":"问题二","methods":["BMI 分组","动态规划"],"pass":"分组推荐时点"},
      {"title":"问题三","methods":["AGE/G/P 协变量","DP 扩展"],"pass":"个性化时点"},
      {"title":"问题四","methods":["Z 值+FDR","k=2 一致性聚合"],"pass":""}
    ],
    "out": "overall_flowchart.drawio"
  }
纯标准库实现，零依赖；输出 .drawio（drawio 桌面版/网页版可直接打开编辑）。
"""
import sys, os, json, html as _html

C = {
    "box": "#dae8fc", "stroke": "#6c8ebf", "title": "#1a1a1a", "font": 13,
    "chainBox": "#e1f5e1", "chainStroke": "#6ba66b",
}

def esc(t):
    return _html.escape(t).replace("\n", "&#10;")

def make_cell(cid, value, x, y, w, h, fill, stroke, parent="1", vertex=True):
    style = (f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
             f"fontSize={C['font']};verticalAlign=top;spacingTop=8;spacing=6;")
    cell = f'        <mxCell id="{cid}" value="{esc(value)}" style="{style}" vertex="1" parent="{parent}">\n'
    cell += f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>\n'
    cell += "        </mxCell>\n"
    return cell

def make_edge(cid, src, tgt, label=None, parent="1"):
    lab = f' value="{esc(label)}"' if label else ' value=""'
    style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;"
             "fontSize=11;strokeColor=#555555;")
    cell = f'        <mxCell id="{cid}"{lab} style="{style}" edge="1" parent="{parent}" source="{src}" target="{tgt}">\n'
    cell += '          <mxGeometry relative="1" as="geometry"/>\n'
    cell += "        </mxCell>\n"
    return cell

def gen_stages(spec):
    titles = spec["stageTitles"]; stages = spec["stages"]; labels = spec.get("edgeLabels") or []
    n = len(titles)
    W, GAP, X0, Y0 = 220, 60, 40, 90
    cells, ids = [], []
    for i, (t, items) in enumerate(zip(titles, stages)):
        x = X0 + i * (W + GAP)
        h = max(96, 44 + 24 * len(items))
        val = t + "\n" + "\n".join("• " + s for s in items)
        cid = f"stage{i}"
        cells.append(make_cell(cid, val, x, Y0, W, h, C["box"], C["stroke"]))
        ids.append(cid)
    for i in range(n - 1):
        cells.append(make_edge(f"e{i}", ids[i], ids[i+1], labels[i] if i < len(labels) else None))
    Wtotal = X0 * 2 + n * W + (n - 1) * GAP
    Htotal = Y0 + max(96, 44 + 24 * max(len(s) for s in stages)) + 60
    return "".join(cells), Wtotal, Htotal

def gen_chain(spec):
    chain = spec["chain"]
    n = len(chain)
    W, GAP, X0, Y0 = 230, 80, 40, 90
    cells, ids = [], []
    for i, q in enumerate(chain):
        x = X0 + i * (W + GAP)
        items = ["• " + m for m in q["methods"]]
        if q.get("pass"):
            items.append("↓ 传递：" + q["pass"])
        h = max(110, 44 + 24 * len(items))
        val = q["title"] + "\n" + "\n".join(items)
        cid = f"q{i}"
        cells.append(make_cell(cid, val, x, Y0, W, h, C["chainBox"], C["chainStroke"]))
        ids.append(cid)
    for i in range(n - 1):
        cells.append(make_edge(f"e{i}", ids[i], ids[i+1], chain[i].get("pass") or None))
    Wtotal = X0 * 2 + n * W + (n - 1) * GAP
    Htotal = Y0 + max(110, 44 + 24 * max(len(q["methods"]) + (1 if q.get("pass") else 0) for q in chain)) + 60
    return "".join(cells), Wtotal, Htotal

def to_mermaid(spec):
    if spec["kind"] == "stages":
        lines = ["flowchart LR"]
        ids = []
        for i, (t, items) in enumerate(zip(spec["stageTitles"], spec["stages"])):
            node = f'N{i}["{t}<br/>' + "<br/>".join(items) + '"]'
            lines.append("  " + node); ids.append(f"N{i}")
        for i in range(len(ids) - 1):
            lab = spec.get("edgeLabels")[i] if i < len(spec.get("edgeLabels") or []) else ""
            lines.append(f"  {ids[i]} -->|{lab}| {ids[i+1]}" if lab else f"  {ids[i]} --> {ids[i+1]}")
        return "\n".join(lines)
    lines = ["flowchart LR"]
    ids = []
    for i, q in enumerate(spec["chain"]):
        node = f'C{i}["{q["title"]}<br/>' + "<br/>".join(q["methods"]) + '"]'
        lines.append("  " + node); ids.append(f"C{i}")
    for i in range(len(ids) - 1):
        lab = spec["chain"][i].get("pass") or ""
        lines.append(f"  {ids[i]} -->|{lab}| {ids[i+1]}" if lab else f"  {ids[i]} --> {ids[i+1]}")
    return "\n".join(lines)

def wrap(xml_body, w, h, name):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" modified="2026-01-01T00:00:00.000Z" agent="flowchart_gen" version="24.0.0">\n'
        f'  <diagram id="d1" name="{esc(name)}">\n'
        f'    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{w+40}" pageHeight="{h+40}" math="0" shadow="0">\n'
        "      <root>\n"
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        + xml_body +
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>\n"
    )

def render_png(spec, out_png, dpi=150):
    """matplotlib 渲染 PNG（中文安全），供 vision-ocr 复核节点文字；无需 drawio CLI。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
    plt.rcParams["axes.unicode_minus"] = False

    if spec["kind"] == "stages":
        titles, stages = spec["stageTitles"], spec["stages"]
        n = len(titles)
        W, GAP, X0, Y0 = 2.4, 0.7, 0.3, 0.4
        max_items = max(len(s) for s in stages)
        H = 0.95 + 0.26 * max_items
        fig_w = X0 * 2 + n * W + (n - 1) * GAP
        fig, ax = plt.subplots(figsize=(fig_w, H + 1.0))
        ax.set_xlim(0, fig_w); ax.set_ylim(0, H + 1.0); ax.axis("off")
        boxes = []
        for i, (t, items) in enumerate(zip(titles, stages)):
            x = X0 + i * (W + GAP); y = 0.5
            h = 0.65 + 0.26 * len(items)
            boxes.append((x, y, W, h))
            ax.add_patch(FancyBboxPatch((x, y), W, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                        fc="#dae8fc", ec="#6c8ebf", lw=1.6))
            ax.text(x + W / 2, y + h - 0.13, t, ha="center", va="top", fontsize=12, fontweight="bold")
            for j, s in enumerate(items):
                ax.text(x + 0.12, y + h - 0.42 - 0.26 * j, "• " + s, ha="left", va="top", fontsize=10.5)
        for i in range(n - 1):
            x1 = boxes[i][0] + boxes[i][2]; y1 = boxes[i][1] + boxes[i][3] / 2
            x2 = boxes[i + 1][0]; y2 = y1
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                                         color="#555555", lw=1.4))
            lab = (spec.get("edgeLabels") or [None] * (n - 1))[i]
            if lab:
                ax.text((x1 + x2) / 2, y1 + 0.15, lab, ha="center", fontsize=9.5, color="#333333")
        ax.set_title(spec.get("title", ""), fontsize=13, fontweight="bold", pad=10)
    else:
        chain = spec["chain"]
        n = len(chain)
        W, GAP, X0, Y0 = 2.5, 0.9, 0.3, 0.4
        max_lines = max(len(q["methods"]) + (1 if q.get("pass") else 0) for q in chain)
        H = 0.95 + 0.26 * max_lines
        fig_w = X0 * 2 + n * W + (n - 1) * GAP
        fig, ax = plt.subplots(figsize=(fig_w, H + 1.0))
        ax.set_xlim(0, fig_w); ax.set_ylim(0, H + 1.0); ax.axis("off")
        boxes = []
        for i, q in enumerate(chain):
            x = X0 + i * (W + GAP); y = 0.5
            lines = q["methods"] + (["↓ 传递：" + q["pass"]] if q.get("pass") else [])
            h = 0.65 + 0.26 * len(lines)
            boxes.append((x, y, W, h))
            ax.add_patch(FancyBboxPatch((x, y), W, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                        fc="#e1f5e1", ec="#6ba66b", lw=1.6))
            ax.text(x + W / 2, y + h - 0.13, q["title"], ha="center", va="top", fontsize=12, fontweight="bold")
            for j, s in enumerate(lines):
                ax.text(x + 0.12, y + h - 0.42 - 0.26 * j, "• " + s, ha="left", va="top", fontsize=10.5)
        for i in range(n - 1):
            x1 = boxes[i][0] + boxes[i][2]; y1 = boxes[i][1] + boxes[i][3] / 2
            x2 = boxes[i + 1][0]; y2 = y1
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                                         color="#555555", lw=1.4))
            lab = chain[i].get("pass")
            if lab:
                ax.text((x1 + x2) / 2, y1 + 0.15, lab, ha="center", fontsize=9.5, color="#333333")
        ax.set_title(spec.get("title", ""), fontsize=13, fontweight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(out_png, dpi=dpi, facecolor="white")
    plt.close(fig)
    return out_png

def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    body, w, h = gen_stages(spec) if spec["kind"] == "stages" else gen_chain(spec)
    out = spec.get("out") or ("flowchart.drawio")
    with open(out, "w", encoding="utf-8") as f:
        f.write(wrap(body, w, h, spec.get("title", "flowchart")))
    mmd_out = os.path.splitext(out)[0] + ".mmd"
    with open(mmd_out, "w", encoding="utf-8") as f:
        f.write(to_mermaid(spec) + "\n")
    png_out = os.path.splitext(out)[0] + ".png"
    render_png(spec, png_out)
    print(f"已生成: {out} | mermaid 预览 {mmd_out} | PNG(供 OCR 复核/直接插图) {png_out}")

if __name__ == "__main__":
    main()
