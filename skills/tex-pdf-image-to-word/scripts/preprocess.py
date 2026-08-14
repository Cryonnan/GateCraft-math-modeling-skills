# -*- coding: utf-8 -*-
"""预处理：剥离 ctexart 版式命令，处理编号引用，输出 pandoc 可解析的干净 tex
用法: python preprocess.py [input.tex] [output.tex] [labels.json]"""
import re, json, sys, os

SRC = sys.argv[1] if len(sys.argv) > 1 else r'NIPT_paper_v7_final.tex'
OUT = sys.argv[2] if len(sys.argv) > 2 else r'paper_clean.tex'
MAP = sys.argv[3] if len(sys.argv) > 3 else r'labels.json'

lines = open(SRC, encoding='utf-8').read().splitlines()

drop_re = [
    r'^% !TEX', r'^\\documentclass', r'^\\usepackage', r'^\\captionsetup',
    r'^\\lstset', r'^\\ctexset', r'^\\pagestyle', r'^\\fancyhf', r'^\\fancyfoot',
    r'^\\renewcommand', r'^\\numberwithin', r'^\\setlength', r'^\\onehalfspacing',
    r'^\\indentfirst', r'^\\vspace', r'^\\hypersetup', r'^\\geometry',
]
drop_c = re.compile('|'.join(drop_re))
size_re = re.compile(r'\\(Large|large|normalsize|small|footnotesize|scriptsize|tiny)\b')

def fix_heiti(line):
    line = re.sub(r'\{\s*\\heiti\s*(?:\\Large\s*)?(\\textbf\{[^{}]*\})\}', r'\1', line)
    line = re.sub(r'\{\s*\\heiti\s*([^{}]*?)\}', r'\\textbf{\1}', line)
    return line.replace('\\heiti', '')

keep = []
appendix = False
in_bib = False
sec = [0, 0, 0]
fig_c = tab_c = eq_c = 0
in_table = in_figure = False
fig_map, tab_map, eq_map = {}, {}, {}

def sec_top():
    return 'A' if appendix and sec[0] > 0 else (str(sec[0]) if sec[0] > 0 else '')

for raw in lines:
    line = raw

    # ---- thebibliography 转手动编号条目 ----
    if re.match(r'^\s*\\begin\{thebibliography\}', line.strip()):
        keep.append('\\section{参考文献}')
        keep.append('')
        in_bib = True
        continue
    if re.match(r'^\s*\\end\{thebibliography\}', line.strip()):
        in_bib = False
        keep.append('')
        continue
    if in_bib and re.match(r'^\s*\\bibitem\{', line.strip()):
        m = re.search(r'\{ref(\d+)\}', line)
        n = m.group(1) if m else '?'
        content = re.sub(r'^\s*\\bibitem\{[^}]*\}\s*', '', line)
        content = content.replace('--', '–').replace('%', r'\%')
        keep.append('\\noindent \\textbf{[%s]} %s' % (n, content))
        continue
    if in_bib:
        continue  # 参考文献内部其余行（空行、注释）跳过

    # ---- 附录标记（含 \newpage\appendix 同行情况） ----
    if r'\appendix' in line:
        appendix = True
        continue
    if re.match(r'^\s*\\section\{附录', line.strip()):
        appendix = True

    if drop_c.match(line.strip()):
        continue

    line = fix_heiti(line)
    line = line.replace('\\S', '§')
    line = size_re.sub('', line)

    m = re.match(r'^\s*\\begin\{lstlisting\}(\[.*\])?', line)
    if m:
        cm = re.search(r'caption=\{(.*?)\}', line)
        if cm:
            cap = cm.group(1).replace('\\texttt{', '').replace('{', '').replace('}', '').replace('\\_', '_')
            keep.append('\\textbf{代码：' + cap + '}')
        keep.append('\\begin{lstlisting}')
        continue

    if re.search(r'\\begin\{table\}', line): tab_c += 1; in_table = True
    if re.search(r'\\begin\{figure\}', line): fig_c += 1; in_figure = True
    if re.search(r'\\end\{table\}', line): in_table = False
    if re.search(r'\\end\{figure\}', line): in_figure = False
    if re.search(r'\\begin\{equation\}', line): eq_c += 1

    # 标题仅切分，不写自动编号（自动编号交给 Word 样式 numPr）
    for cmd, level in ((r'\\section', 0), (r'\\subsection', 1), (r'\\subsubsection', 2)):
        if re.match(r'^\s*' + cmd + r'\{', line):
            sec[level] += 1
            for lv in range(level + 1, 3): sec[lv] = 0
            if level == 0: eq_c = 0
            break

    def cap_sub(mo):
        pre = ''
        if in_table: pre = f'表 {sec_top()}.{tab_c} '
        elif in_figure: pre = f'图 {sec_top()}.{fig_c} '
        return '\\caption{' + pre + mo.group(1) + '}'
    line = re.sub(r'\\caption\{([^}]*)\}', cap_sub, line, count=1)

    for lm in re.finditer(r'\\label\{(fig|tab|eq):([^}]+)\}', line):
        kind, name = lm.group(1), lm.group(2)
        num = f'{sec_top()}.{fig_c if kind == "fig" else (tab_c if kind == "tab" else eq_c)}'
        (fig_map if kind == 'fig' else tab_map if kind == 'tab' else eq_map)[name] = num

    if re.match(r'^\s*\\label\{eq:', line.strip()):
        continue

    def ref_sub(mo):
        name = mo.group(1)
        for kind, m in (('fig', fig_map), ('tab', tab_map), ('eq', eq_map)):
            if name.startswith(kind + ':'):
                k = name[len(kind) + 1:]
                return m.get(k, mo.group(0))
        return mo.group(0)
    line = re.sub(r'\\ref\{([^}]+)\}', ref_sub, line)
    line = re.sub(r'\\cite\{ref(\d+)\}', r'[\1]', line)

    # 圆圈编号：技术路线顺叙去编号；其余 \textcircled{n} 统一为 (n)
    if '技术路线' in line and re.search(r'\\textcircled\{', line):
        line = re.sub(r'\s*\\textcircled\{\w+\}', '', line)
        line = line.replace('为：', '为：') if '为：' in line else line
    else:
        line = re.sub(r'\\textcircled\{(\w+)\}', r'(\1)', line)

    if '$' not in line:
        line = line.replace('\\quad', ' ')

    keep.append(line)

open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(keep))
json.dump({'fig': fig_map, 'tab': tab_map, 'eq': eq_map},
          open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('sections:', sec, '| fig:', fig_c, '| tab:', tab_c, '| eq:', eq_c)
print('tab_map:', tab_map)