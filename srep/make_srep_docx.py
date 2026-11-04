"""
Build the single column Word file from srep/manuscript.tex.

  * %%TABLE eaai:<label>%% and %%FIGURE eaai:<label>%% copy that table or figure from
    eaai/manuscript.tex, so the numbers are the checked ones.
  * %%GENTABLE dataset|hyper|signif%% builds a table from the data and result files.
  * Sections, tables, figures and citations are numbered in order of appearance.
  * References are formatted in the Nature style from srep/references.bib.

    python srep/make_srep_docx.py            # writes OrbitGuard_SciRep.docx in the repo root
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor, Cm

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "OrbitGuard_SciRep.docx"
REPORTS = REPO / "reports"

src = (HERE / "manuscript.tex").read_text()
eaai = (REPO / "eaai" / "manuscript.tex").read_text()


# ── 1. pull shared tables and figures, build generated tables ───────────────
def env_with_label(text, kind, label):
    for m in re.finditer(r"\\begin\{(" + kind + r"\*?)\}.*?\\end\{\1\}", text, re.S):
        if "\\label{" + label + "}" in m.group(0):
            return m.group(0)
    raise KeyError(label)


def gen_dataset():
    econ = {p["planet"]: p for p in json.loads((REPORTS / "prune_economics.json").read_text())["per_planet"]}
    rows = []
    for p in ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]:
        z = np.load(REPO / "data" / "per_planet" / f"{p}.npz")
        y = z["y"]
        group = "inner" if p in ("mercury", "venus", "mars") else "outer"
        rows.append(f"{p.capitalize()} & {group} & {len(y):,} & {100 * (y == 0).mean():.1f}\\% & {int(round(z['lengths'].mean()))} & {econ[p]['prop_days']:,.0f} \\\\")
    return ("\\begin{table}\n\\caption{The simulated missions of each target. Failure share is the share of missions labeled as failures. "
            "Steps is the mean number of telemetry steps per mission after downsampling. Flight time is the mean simulated flight time, "
            "which is also the propagation cost that the screen tries to save.}\n\\label{tab:dataset}\n\\begin{tabular}{llcccc}\n\\toprule\n"
            "Target & Group & Missions & Failure share & Steps & Flight time (days) \\\\\n\\midrule\n" + "\n".join(rows) +
            "\n\\bottomrule\n\\end{tabular}\n\\end{table}")


def gen_hyper():
    rows = [
        ("Encoder", "Transformer, pre-layer normalization, CLS token"),
        ("Width, heads, layers", "128, 8, 4 (feed-forward size 512, dropout 0.1)"),
        ("Output heads", "failure probability, and failure type (loss weight 0.5)"),
        ("Loss", "binary cross-entropy weighted for class balance"),
        ("Optimizer", "AdamW, learning rate 0.001, weight decay 0.0001"),
        ("Schedule", "cosine annealing, 60 epochs, batch size 128"),
        ("Gradient clipping", "norm 1.0"),
        ("Training prefixes", "random length, 5\\% to 40\\% of each flight"),
        ("Failure-type sampling", "weights proportional to (1/count)\\textsuperscript{0.5}"),
        ("Model selection", "best validation AUC"),
        ("Baseline", "XGBoost, 300 trees, depth 5, learning rate 0.08"),
        ("Second dataset", "same Transformer, 20 epochs, batch size 256, window and horizon of 30 cycles"),
    ]
    body = "\n".join(f"{a} & {b} \\\\" for a, b in rows)
    return ("\\begin{table}\n\\caption{Training settings. The same settings are used for all three scaling modes.}\n\\label{tab:hyper}\n"
            "\\begin{tabular}{ll}\n\\toprule\nSetting & Value \\\\\n\\midrule\n" + body + "\n\\bottomrule\n\\end{tabular}\n\\end{table}")


def gen_signif():
    s = json.loads((REPORTS / "significance.json").read_text())
    welch = {w["planet"]: w for w in s["welch_across_seeds"]}
    rows = []
    for p in ["venus", "mars", "mercury", "jupiter"]:
        r = [x for x in s["per_run"] if x["planet"] == p and x["seed"] == 42][0]
        w = welch[p]

        def pv(v):
            return "<0.001" if v < 0.001 else f"{v:.3f}"
        rows.append(f"{p.capitalize()} & {r['auc_per_timestep']:.4f} ({r['ci_per_timestep'][0]:.4f} to {r['ci_per_timestep'][1]:.4f}) & "
                    f"{r['auc_grouped']:.4f} ({r['ci_grouped'][0]:.4f} to {r['ci_grouped'][1]:.4f}) & "
                    f"{r['diff']:.4f} ({r['ci_diff'][0]:.4f} to {r['ci_diff'][1]:.4f}) & {r['mcnemar_b']}/{r['mcnemar_c']}, {pv(r['mcnemar_p'])} & "
                    f"{w['t']:.2f}, {pv(w['p'])} \\\\")
    return ("\\begin{table}\n\\caption{Per timestep against grouped scaling on the same test missions. AUC values and 95\\% bootstrap intervals "
            "(2,000 resamples) are for seed 42. McNemar gives the number of missions that only the per timestep model gets right and the number "
            "that only the grouped model gets right, with the exact p value. Welch gives t and p for the test AUC across the five seeds.}\n"
            "\\label{tab:signif}\n\\begin{tabular}{lccccc}\n\\toprule\n"
            "Target & Per timestep AUC & Grouped AUC & Difference & McNemar & Welch \\\\\n\\midrule\n" + "\n".join(rows) +
            "\n\\bottomrule\n\\end{tabular}\n\\end{table}")


GEN = {"dataset": gen_dataset, "hyper": gen_hyper, "signif": gen_signif}
src = "\n".join(l for l in src.split("\n") if not l.startswith("%%") or re.match(r"%%(TABLE|FIGURE|GENTABLE) ", l))
text = re.sub(r"%%TABLE eaai:([^%]+)%%", lambda m: env_with_label(eaai, "table", m.group(1)), src)
text = re.sub(r"%%FIGURE eaai:([^%]+)%%", lambda m: env_with_label(eaai, "figure", m.group(1)), text)
text = re.sub(r"%%GENTABLE (\w+)%%", lambda m: GEN[m.group(1)](), text)
text = text.replace("\\citep{", "\\cite{")
text = "\n".join(l for l in text.split("\n") if not l.lstrip().startswith("%"))

# American spelling for the text pulled from the British source; file names and labels are left alone
AMERICAN = [("NORMALISATION", "NORMALIZATION"), ("Normalisation", "Normalization"), ("normalisations", "normalizations"),
            ("normalisation", "normalization"), ("normalised", "normalized"), ("labelled", "labeled"), ("behaviour", "behavior"),
            ("initialisation", "initialization"), ("artefacts", "artifacts"), ("artefact", "artifact"), ("unmodelled", "unmodeled"),
            ("modelling", "modeling"), ("optimiser", "optimizer"), ("categorised", "categorized"), ("summarised", "summarized"),
            ("levelling", "leveling"), ("generalises", "generalizes"), ("standardisation", "standardization"),
            ("neighbourhood", "neighborhood"), ("whilst", "while"), ("centres", "centers")]
keep = re.compile(r"\\includegraphics(\[[^\]]*\])?\{[^}]*\}|\\label\{[^}]*\}|\\ref\{[^}]*\}|\\cite\{[^}]*\}")
parts, last = [], 0
for m in keep.finditer(text):
    seg = text[last:m.start()]
    for o, n in AMERICAN:
        seg = seg.replace(o, n)
    parts += [seg, m.group(0)]
    last = m.end()
seg = text[last:]
for o, n in AMERICAN:
    seg = seg.replace(o, n)
text = "".join(parts + [seg])

# ── 2. numbering ────────────────────────────────────────────────────────────
title = re.search(r"\\title\{(.*?)\}", text).group(1)
abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.S).group(1).strip()
keywords = re.search(r"\\begin\{keywords\}(.*?)\\end\{keywords\}", text, re.S).group(1).strip()
body = text[text.index("\\section{Introduction}"):]

LABELS = {}
sec = sub = 0
for m in re.finditer(r"\\(section|subsection)(\*?)\{([^}]*)\}(\s*\\label\{([^}]*)\})?", body):
    if m.group(2):
        continue
    if m.group(1) == "section":
        sec += 1; sub = 0; num = str(sec)
    else:
        sub += 1; num = f"{sec}.{sub}"
    if m.group(5):
        LABELS[m.group(5)] = num
for i, m in enumerate(re.finditer(r"\\begin\{table\*?\}.*?\\label\{([^}]*)\}", body, re.S), 1):
    LABELS[m.group(1)] = str(i)
for i, m in enumerate(re.finditer(r"\\begin\{figure\*?\}.*?\\label\{([^}]*)\}", body, re.S), 1):
    LABELS[m.group(1)] = str(i)

order = []
for m in re.finditer(r"\\cite\{([^}]*)\}", body):
    for k in m.group(1).split(","):
        k = k.strip()
        if k not in order:
            order.append(k)
CITE = {k: i + 1 for i, k in enumerate(order)}


def cite_str(keys):
    nums = sorted(CITE[k.strip()] for k in keys.split(","))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"{nums[i]}\u2013{nums[j]}" if j - i >= 2 else ",".join(str(n) for n in nums[i:j + 1]))
        i = j + 1
    return ",".join(out)


# ── 3. LaTeX to runs ────────────────────────────────────────────────────────
SUPMAP = str.maketrans("-0123456789", "\u207b\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079")


def braced(m, i):
    """Content of the balanced {...} that starts at m[i], and the index after it."""
    depth = 0
    for j in range(i, len(m)):
        if m[j] == "{":
            depth += 1
        elif m[j] == "}":
            depth -= 1
            if depth == 0:
                return m[i + 1:j], j + 1
    raise ValueError(m)


def math_runs(m, base):
    out, i = [], 0
    m = m.replace("\\,", " ")
    while i < len(m):
        c = m[i]
        if m.startswith("\\hat{", i):
            arg, i = braced(m, i + 4); out.append((arg + "\u0302", dict(base, italic=True)))
        elif m.startswith("\\mathrm{", i) or m.startswith("\\operatorname{", i):
            arg, i = braced(m, m.index("{", i)); out.append((arg, dict(base)))
        elif c == "\\":
            mm = re.match(r"\\([A-Za-z]+)", m[i:])
            if mm is None:
                out.append((m[i + 1], dict(base))); i += 2; continue
            i += len(mm.group(0))
            out.append(({"mid": " | ", "in": " \u2208 ", "pm": "\u00b1", "epsilon": "\u03b5", "le": "\u2264", "ge": "\u2265",
                         "times": "\u00d7"}.get(mm.group(1), ""), dict(base, italic=mm.group(1) == "epsilon")))
        elif c in "{}":
            i += 1
        elif c in "_^":
            if m[i + 1] == "{":
                arg, i = braced(m, i + 1)
            else:
                arg = m[i + 1]; i += 2
            if c == "_":
                sub = math_runs(arg, dict(base, sub=True))
                out.extend(sub)
            else:
                out.append((arg, dict(base, sup=True)))
        elif c.isalpha():
            out.append((c, dict(base, italic=True) if not base.get("sub") else dict(base))); i += 1
        else:
            out.append((c, dict(base))); i += 1
    return out


def inline(s, base=None):
    base = base or {}
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = re.sub(r"(Section|Sections|Table|Fig\.|Figure)~\\ref\{([^}]*)\}", lambda m: f"{m.group(1)} {LABELS[m.group(2)]}", s)
    s = re.sub(r"\s*\\cite\{([^}]*)\}", lambda m: "\x01" + cite_str(m.group(1)) + "\x02", s)
    s = re.sub(r"\\texttt\{([^}]*)\}", lambda m: m.group(1).replace("\\_", "_"), s)
    s = s.replace("\\_", "_").replace("\\%", "%").replace("\\&", "&").replace("~", "\u00a0")
    s = s.replace("---", "\u2014").replace("--", "\u2013")
    s = s.replace("``", "\u201c").replace("''", "\u201d")
    s = re.sub(r"(?<![A-Za-z0-9])`([^`']*)'", "\u2018\\1\u2019", s)
    s = re.sub(r'"([^"]*)"', "\u201c\\1\u201d", s)
    s = s.replace("'", "\u2019")
    runs, pos = [], 0
    pat = re.compile(r"\\textbf\{([^}]*)\}|\\textsuperscript\{([^}]*)\}|\$([^$]*)\$|\x01([^\x02]*)\x02")
    for m in pat.finditer(s):
        if m.start() > pos:
            runs.append((s[pos:m.start()], dict(base)))
        if m.group(1) is not None:
            runs.append((m.group(1), dict(base, bold=True)))
        elif m.group(2) is not None:
            runs.append((m.group(2), dict(base, sup=True)))
        elif m.group(3) is not None:
            runs.extend(math_runs(m.group(3), base))
        else:
            runs.append((m.group(4), dict(base, sup=True)))
        pos = m.end()
    if pos < len(s):
        runs.append((s[pos:], dict(base)))
    merged = []
    for t, f in runs:
        t = re.sub(r"[ \n]+", " ", t)
        if merged and merged[-1][1] == f:
            merged[-1] = (merged[-1][0] + t, f)
        else:
            merged.append((t, f))
    return merged


# ── 4. the Word document ────────────────────────────────────────────────────
d = Document()
sec0 = d.sections[0]
sec0.page_width, sec0.page_height = Cm(21.0), Cm(29.7)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec0, side, Inches(1))
TEXT_W = 21.0 / 2.54 - 2.0          # inches

FONT = "Times New Roman"
st = d.styles["Normal"]
st.font.name = FONT; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
st.paragraph_format.line_spacing = 1.5
st.paragraph_format.space_after = Pt(6)
for name, size in (("Heading 1", 14), ("Heading 2", 12), ("Title", 16)):
    h = d.styles[name]
    h.font.name = FONT; h.font.size = Pt(size); h.font.bold = True; h.font.italic = False
    h.font.color.rgb = RGBColor(0, 0, 0)
    rpr = h.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    h.paragraph_format.space_before = Pt(12 if name != "Title" else 0)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.line_spacing = 1.15
d.styles["Heading 2"].font.italic = False


def add_runs(p, runs, size=None):
    for t, f in runs:
        r = p.add_run(t)
        if f.get("bold"): r.bold = True
        if f.get("italic"): r.italic = True
        if f.get("sub"): r.font.subscript = True
        if f.get("sup"): r.font.superscript = True
        if size: r.font.size = Pt(size)
    return p


def para(runs, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=None, style=None):
    p = d.add_paragraph(style=style)
    p.alignment = align
    return add_runs(p, runs, size)


# title block
t = d.add_paragraph(style="Title"); t.alignment = WD_ALIGN_PARAGRAPH.CENTER; t.add_run(title)
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
for i, nm in enumerate(["Harsha Vardan M Sakamuri", "Rohit Michael Raj", "Valarmathi P."]):
    p.add_run(nm)
    r = p.add_run("1" + ("*" if nm.startswith("Valarmathi") else "")); r.font.superscript = True
    if i < 2:
        p.add_run(", ")
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("1"); r.font.superscript = True
r = p.add_run("School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai 600127, India"); r.italic = True
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run("*Corresponding author: valarmathi.sudhakar@vit.ac.in")

d.add_paragraph("Abstract", style="Heading 1")
para(inline(abstract))
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
r = p.add_run("Keywords: "); r.bold = True
p.add_run(keywords.replace(";", ","))


def set_cell_border(cell, **kw):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders"); tcPr.append(b)
    for edge, val in kw.items():
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), val); e.set(qn("w:sz"), "8"); e.set(qn("w:color"), "000000"); e.set(qn("w:space"), "0")
        b.append(e)


def parse_tabular(block):
    inner = re.search(r"\\toprule(.*?)\\bottomrule", block, re.S).group(1)
    inner = re.sub(r"\\cmidrule(\([a-z]+\))?\{[^}]*\}", "", inner)
    lines = [ln for ln in re.split(r"\\\\", inner.replace("\\midrule", "\\\\")) if ln.strip()]
    rows = []
    for ln in lines:
        cells = []
        for c in ln.strip().split("&"):
            c = c.strip()
            m = re.match(r"\\multicolumn\{(\d+)\}\{[a-z]\}\{(.*)\}$", c, re.S)
            cells.append(dict(text=m.group(2), span=int(m.group(1))) if m else dict(text=c, span=1))
        rows.append(cells)
    return rows


def add_table(block):
    cap = re.search(r"\\caption\{(.*?)\}\s*\\label\{([^}]*)\}", block, re.S)
    num = LABELS[cap.group(2)]
    cp = d.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    cp.paragraph_format.keep_with_next = True; cp.paragraph_format.line_spacing = 1.15
    r = cp.add_run(f"Table {num}. "); r.bold = True; r.font.size = Pt(10)
    add_runs(cp, inline(cap.group(1)), size=10)
    rows = parse_tabular(block)
    ncol = max(sum(c["span"] for c in r_) for r_ in rows)
    tb = d.add_table(rows=len(rows), cols=ncol)
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    tb.autofit = True
    size = 9 if ncol <= 6 else 8
    nhead = 2 if any(c["span"] > 1 for c in rows[0]) else 1
    numeric = re.compile(r"^[\s\d.,%()$\\a-z/<>+\-]*$")
    col_numeric = [True] * ncol
    for r_ in rows[nhead:]:
        cc = 0
        for c in r_:
            txt = c["text"].strip()
            if c["span"] == 1 and txt not in ("none", "n/a") and not re.fullmatch(r"[\d\s.,%()<>+/\-]*(e-?\d+)?[\d\s.,%()<>+/\-]*(to[\d\s.,%()e\-]*)?|\$?[\d.]+\s*\\pm\s*[\d.]+\$?|[\d/]+, ?[<\d.]+|[\d.\-]+, ?[<\d.e\-]+", txt):
                col_numeric[cc] = False
            cc += c["span"]
    for ri, row in enumerate(rows):
        col = 0
        for c in row:
            cell = tb.cell(ri, col)
            if c["span"] > 1:
                cell = cell.merge(tb.cell(ri, col + c["span"] - 1))
            cell.text = ""
            p_ = cell.paragraphs[0]
            p_.paragraph_format.line_spacing = 1.0; p_.paragraph_format.space_after = Pt(1)
            p_.paragraph_format.keep_with_next = ri < len(rows) - 1
            p_.alignment = WD_ALIGN_PARAGRAPH.CENTER if (c["span"] > 1 or col_numeric[col]) else WD_ALIGN_PARAGRAPH.LEFT
            add_runs(p_, [(tx, dict(f, bold=f.get("bold") or ri < nhead)) for tx, f in inline(c["text"])], size=size)
            edges = {}
            if ri == 0:
                edges["top"] = "single"
            if ri == nhead - 1:
                edges["bottom"] = "single"
            if ri == len(rows) - 1:
                edges["bottom"] = "single"
            if edges:
                set_cell_border(cell, **edges)
            col += c["span"]
    d.add_paragraph().paragraph_format.space_after = Pt(2)


WIDTH = {"fig_pipeline.png": 6.2, "fig1.png": 6.0, "fig2.png": 6.2, "fig3.png": 4.3, "fig4.png": 4.3, "fig5.png": 4.3, "fig6.png": 6.0}


def add_figure(block):
    png = re.search(r"\\includegraphics(\[[^\]]*\])?\{([^}]*)\}", block).group(2)
    path = HERE / png if (HERE / png).exists() else REPO / "eaai" / png
    cap = re.search(r"\\caption\{(.*?)\}\s*\\label\{([^}]*)\}", block, re.S)
    ip = d.add_paragraph(); ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ip.paragraph_format.keep_with_next = True
    ip.add_run().add_picture(str(path), width=Inches(min(WIDTH.get(png, 5.5), TEXT_W)))
    cp = d.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; cp.paragraph_format.line_spacing = 1.15
    r = cp.add_run(f"Figure {LABELS[cap.group(2)]}. "); r.bold = True; r.font.size = Pt(10)
    add_runs(cp, inline(cap.group(1)), size=10)


def add_equation(block, n):
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.tab_stops.add_tab_stop(Inches(TEXT_W / 2), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Inches(TEXT_W), WD_TAB_ALIGNMENT.RIGHT)
    add_runs(p, [("\t", {})] + math_runs(" ".join(block.split()).rstrip(",. "), {}) + [(f"\t({n})", {})])


# ── 5. references in Nature style ───────────────────────────────────────────
bibtxt = (HERE / "references.bib").read_text()
BIB = {}
for typ, key, bodytxt in re.findall(r"@(\w+)\{([^,]+),(.*?)\n\}", bibtxt, re.S):
    f = {k.lower(): " ".join(v.split()) for k, v in re.findall(r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", bodytxt)}
    f["type"] = typ.lower()
    BIB[key.strip()] = f
ACC = {r"{\~o}": "õ", r"{\'i}": "í", r"{\'a}": "á", r'{\"u}': "ü", r'{\"a}': "ä", r"{\'e}": "é", r'{\"o}': "ö"}


def clean(s):
    for a, b in ACC.items():
        s = s.replace(a, b)
    s = s.replace("\\&", "&").replace("--", "\u2013")
    return re.sub(r"[{}]", "", s)


def ref_runs(k):
    f = BIB[k]
    authors = [a.strip() for a in clean(f.get("author", "")).split(" and ")]
    if len(authors) > 5 or "others" in authors:
        au = authors[0] + " et al."
    elif len(authors) > 1:
        au = ", ".join(authors[:-1]) + " & " + authors[-1]
    else:
        au = authors[0]
    runs = [(au + " ", {}), (clean(f.get("title", "")).rstrip(".") + ". ", {})]
    venue = clean(f.get("journal") or f.get("booktitle") or "")
    if f["type"] == "inproceedings":
        runs.append(("In ", {}))
    runs.append((venue, dict(italic=True)))
    if f.get("volume"):
        runs += [(" ", {}), (f["volume"], dict(bold=True))]
    if f.get("pages"):
        runs.append((", " + clean(f["pages"]), {}))
    runs.append((f" ({f.get('year', '')}).", {}))
    if f.get("doi"):
        runs.append((" https://doi.org/" + f["doi"], {}))
    return runs


# ── 6. body ─────────────────────────────────────────────────────────────────
SCAN = re.compile(r"\\section(\*?)\{([^}]*)\}|\\subsection\{([^}]*)\}|\\begin\{(equation|itemize|table\*?|figure\*?)\}")
eq_no = 0
refs_done = False


def write_refs():
    d.add_paragraph("References", style="Heading 1")
    for k in order:
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.15; p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.35); p.paragraph_format.first_line_indent = Inches(-0.35)
        add_runs(p, [(f"{CITE[k]}.\t", {})] + ref_runs(k), size=10)


def paragraphs(chunk):
    for c in re.split(r"\n\s*\n", chunk):
        c = c.strip()
        if c:
            para(inline(c))


pos = 0
while pos < len(body):
    m = SCAN.search(body, pos)
    if not m:
        paragraphs(body[pos:]); break
    paragraphs(body[pos:m.start()])
    pos = m.end()
    if m.group(2) is not None:
        name = m.group(2)
        if m.group(1):
            if name == "Funding" and not refs_done:
                write_refs(); refs_done = True
            d.add_paragraph(name, style="Heading 1")
        else:
            lab = re.match(r"\s*\\label\{([^}]*)\}", body[pos:])
            num = LABELS[lab.group(1)] if lab else ""
            d.add_paragraph(f"{num} {name}".strip(), style="Heading 1")
        lab = re.match(r"\s*\\label\{[^}]*\}", body[pos:])
        if lab:
            pos += lab.end()
    elif m.group(3) is not None:
        lab = re.match(r"\s*\\label\{([^}]*)\}", body[pos:])
        if lab:
            num = LABELS[lab.group(1)]; pos += lab.end()
        else:
            # unlabeled subsection: find its number by position
            k = sum(1 for _ in re.finditer(r"\\section\{", body[:m.start()]))
            j = sum(1 for _ in re.finditer(r"\\subsection\{", body[body.rfind("\\section{", 0, m.start()):m.start()])) + 1
            num = f"{k}.{j}"
        d.add_paragraph(f"{num} {m.group(3)}", style="Heading 2")
    else:
        env = m.group(4)
        end = body.index("\\end{" + env + "}", pos)
        block = body[pos:end]
        pos = end + len("\\end{" + env + "}")
        if env == "equation":
            eq_no += 1; add_equation(block, eq_no)
        elif env == "itemize":
            for item in re.split(r"\\item\s+", block)[1:]:
                p = para(inline(item), style="List Bullet")
        elif env.startswith("table"):
            add_table(block)
        else:
            add_figure(block)
if not refs_done:
    write_refs()

# page numbers in the footer
fp = d.sections[0].footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fp.add_run()
for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if tag:
        e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tag); run._r.append(e)
    else:
        e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; run._r.append(e)

d.save(str(OUT))
unused = sorted(set(BIB) - set(order))
print("saved", OUT, "| citations", len(order), "| bib entries not cited:", unused)
