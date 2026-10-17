"""
Build OrbitGuard_TAES.docx from the OFFICIAL TAES Word template.

The text comes from taes/manuscript_taes.tex (so it is the same text as the PDF).
The look comes from the template: its page size, two columns, footers and paragraph
styles (Title_document, Authors, Affiliation, Abstract, History, Heading 1/2, Para,
DisplayFormula, Image, FigureCaption, TableCaption, ReferenceHead, Bib_entry, AuthorBio).

    python taes/make_taes_word.py [path/to/TAES_Word_Template.zip] [output.docx]
"""

import copy
import io
import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph
from lxml import etree

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ZIP = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs" / "paper" / "TAES_Word_Template.zip"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "OrbitGuard_TAES.docx"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
XML = "{http://www.w3.org/XML/1998/namespace}"

# ── the official template ────────────────────────────────────────────────────
with zipfile.ZipFile(ZIP) as z:
    name = next(n for n in z.namelist() if n.endswith("IEEE_TAES_Regular_template.docx"))
    d = Document(io.BytesIO(z.read(name)))
body = d.element.body
kids0 = list(body.iterchildren())
paras0 = [e for e in kids0 if e.tag == W + "p"]


def ptxt(e):
    return "".join(t.text or "" for t in e.iter(W + "t"))


def find0(style, startswith=""):
    for e in kids0:
        if e.tag != W + "p":
            continue
        ps = e.find(W + "pPr")
        sty = ps.find(W + "pStyle").get(W + "val") if ps is not None and ps.find(W + "pStyle") is not None else ""
        if sty == style and ptxt(e).startswith(startswith):
            return e
    raise KeyError((style, startswith))


T = dict(
    title=find0("Titledocument"), authors=find0("Authors"), affil=find0("Affiliation"),
    abstract=find0("Abstract", "Abstract"), foot=[e for e in kids0 if e.tag == W + "p" and ptxt(e) == "" and e.find(".//" + W + "footnoteReference") is not None][0],
    history=find0("History"), h1=find0("Heading1", "INTRODUCTION"), h2=find0("Heading2", "Abbreviations"),
    para=find0("Para", "This document is a template"), bullet=find0("Para", "punctuation;"),
    formula=find0("DisplayFormula"), image=find0("Image"), figcap=find0("FigureCaption"),
    tabcap=find0("TableCaption"), refhead=find0("ReferenceHead"), bib=find0("Bibentry", "[1]"),
    bio=find0("AuthorBio", "SECOND B."), table=[e for e in kids0 if e.tag == W + "tbl"][0],
)
SECT_MAIN = [e for e in kids0 if e.tag == W + "p" and e.find(W + "pPr") is not None and e.find(W + "pPr").find(W + "sectPr") is not None][0]
sect_main = copy.deepcopy(SECT_MAIN.find(W + "pPr").find(W + "sectPr"))
T = {k: (copy.deepcopy(v) if not isinstance(v, list) else v) for k, v in T.items()}


def strip_ids(e):
    for x in e.iter():
        for a in list(x.attrib):
            if a.endswith("}paraId") or a.endswith("}textId") or "rsid" in a:
                del x.attrib[a]
    return e


# keep only the section-break paragraph and what follows it; everything before is sample text
idx = kids0.index(SECT_MAIN)
for e in kids0[:idx]:
    body.remove(e)
ANCHOR = SECT_MAIN


def clone(key):
    return strip_ids(copy.deepcopy(T[key]))


def add(e):
    ANCHOR.addprevious(e)
    return e


# ── run helpers ──────────────────────────────────────────────────────────────
def mkrun(text, bold=False, italic=False, sub=False, sup=False, size=None, nobold=False):
    r = etree.Element(W + "r")
    rpr = etree.SubElement(r, W + "rPr")
    if bold: etree.SubElement(rpr, W + "b")
    if nobold: etree.SubElement(rpr, W + "b").set(W + "val", "0")
    if italic: etree.SubElement(rpr, W + "i")
    if sub: etree.SubElement(rpr, W + "vertAlign").set(W + "val", "subscript")
    if sup: etree.SubElement(rpr, W + "vertAlign").set(W + "val", "superscript")
    if size:
        etree.SubElement(rpr, W + "sz").set(W + "val", str(int(size * 2)))
        etree.SubElement(rpr, W + "szCs").set(W + "val", str(int(size * 2)))
    if len(rpr) == 0:
        r.remove(rpr)
    parts = text.split("\t")
    for i, part in enumerate(parts):
        if i:
            etree.SubElement(r, W + "tab")
        if part:
            t = etree.SubElement(r, W + "t"); t.text = part; t.set(XML + "space", "preserve")
    return r


def set_runs(p, runs):
    """Replace the runs of paragraph p with (text, fmt) pairs, keeping pPr."""
    for c in list(p):
        if c.tag != W + "pPr":
            p.remove(c)
    for text, fmt in runs:
        p.append(mkrun(text, **fmt))


# ── LaTeX to runs ────────────────────────────────────────────────────────────
SECS, TABS, FIGS = {}, {}, {}
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV"]
SUP = str.maketrans("-0123456789", "\u207b\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079")
CITE_NUM = {}


def cite_text(keys):
    nums = sorted(CITE_NUM[k.strip()] for k in keys.split(","))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        if j - i >= 2:
            out.append(f"[{nums[i]}]\u2013[{nums[j]}]")
        else:
            out.extend(f"[{n}]" for n in nums[i:j + 1])
        i = j + 1
    return ", ".join(out)


def math_runs(m, base):
    """Small subset of LaTeX math, enough for the symbols used in the paper."""
    out = []
    i = 0
    m = m.replace("\\,", "").replace("\\left", "").replace("\\right", "")
    while i < len(m):
        c = m[i]
        if m.startswith("\\hat{", i):
            j = m.index("}", i); out.append((m[i + 5:j] + "\u0302", dict(base, italic=True))); i = j + 1
        elif m.startswith("\\mathrm{", i) or m.startswith("\\operatorname{", i):
            a = m.index("{", i); j = m.index("}", a); out.append((m[a + 1:j], dict(base))); i = j + 1
        elif c == "\\":
            mm = re.match(r"\\([A-Za-z]+)", m[i:])
            if mm is None:                      # an escaped symbol such as \{ or \}
                out.append((m[i + 1], dict(base))); i += 2
                continue
            cmd = mm.group(1); i += len(mm.group(0))
            out.append(({"mid": " | ", "in": " \u2208 ", "pm": "\u00b1", "epsilon": "\u03b5", "le": "\u2264", "ge": "\u2265"}.get(cmd, ""), dict(base)))
        elif c == "\\" or c in "{}":
            i += 1
        elif c == "_" or c == "^":
            if m[i + 1] == "{":
                j = m.index("}", i); arg = m[i + 2:j]; i = j + 1
            else:
                arg = m[i + 1]; i += 2
            if c == "^":
                arg = arg.translate(SUP)
                out.append((arg, dict(base)))
            else:
                out.append((arg, dict(base, sub=True)))
        elif c.isalpha():
            out.append((c, dict(base, italic=True))); i += 1
        else:
            out.append((c, dict(base))); i += 1
    return out


def inline(s, base=None):
    """LaTeX paragraph text to a list of (text, fmt) runs."""
    base = base or {}
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = re.sub(r"(Section|Table|Fig\.)~\\ref\{([^}]*)\}",
               lambda m: {"Section": "Section " + SECS.get(m.group(2), "?"), "Table": "Table " + TABS.get(m.group(2), "?"),
                          "Fig.": "Fig. " + FIGS.get(m.group(2), "?")}[m.group(1)], s)
    s = re.sub(r"\\cite\{([^}]*)\}", lambda m: cite_text(m.group(1)), s)
    s = re.sub(r"\\url\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\texttt\{([^}]*)\}", lambda m: m.group(1).replace("\\_", "_"), s)
    s = s.replace("\\%", "%").replace("\\&", "&").replace("~", "\u00a0").replace("---", "\u2014").replace("--", "\u2013")
    s = s.replace("``", "\u201c").replace("''", "\u201d")
    s = re.sub(r"(?<![A-Za-z])`([^`']*)'", "\u2018\\1\u2019", s)
    s = s.replace("'", "\u2019")
    runs = []
    # split on bold and math
    pos = 0
    pat = re.compile(r"\\textbf\{([^}]*)\}|\$([^$]*)\$")
    for m in pat.finditer(s):
        if m.start() > pos:
            runs.append((s[pos:m.start()], dict(base)))
        if m.group(1) is not None:
            runs.append((m.group(1), dict(base, bold=True)))
        else:
            runs.extend(math_runs(m.group(2), base))
        pos = m.end()
    if pos < len(s):
        runs.append((s[pos:], dict(base)))
    # merge neighbours with equal format, collapse whitespace
    merged = []
    for t, f in runs:
        if merged and merged[-1][1] == f:
            merged[-1] = (merged[-1][0] + t, f)
        else:
            merged.append((t, f))
    return [(re.sub(r"[ \n]+", " ", t), f) for t, f in merged]


# ── read the TAES LaTeX ──────────────────────────────────────────────────────
tex = (HERE / "manuscript_taes.tex").read_text()
title = re.search(r"\\title\{(.*?)\}", tex).group(1)
abstract = inline(re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S).group(1).strip())
keywords = re.search(r"\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}", tex, re.S).group(1).strip()
main = tex[tex.index("\\section{INTRODUCTION}"):tex.index("\\section*{ACKNOWLEDGMENT}")]
ack = tex[tex.index("\\section*{ACKNOWLEDGMENT}") + len("\\section*{ACKNOWLEDGMENT}"):tex.index("\\bibliographystyle")].strip()
bios = re.findall(r"\\begin\{IEEEbiographynophoto\}\{([^}]*)\}\s*(.*?)\s*\\end\{IEEEbiographynophoto\}", tex, re.S)

# numbering: sections, tables, figures and citations in order of appearance
for i, m in enumerate(re.finditer(r"\\section\{[^}]*\}\s*\\label\{([^}]*)\}", main), 1):
    SECS[m.group(1)] = ROMAN[i]
for i, m in enumerate(re.finditer(r"\\begin\{table\*?\}.*?\\label\{([^}]*)\}", main, re.S), 1):
    TABS[m.group(1)] = ROMAN[i]
for i, m in enumerate(re.finditer(r"\\begin\{figure\*?\}.*?\\label\{([^}]*)\}", main, re.S), 1):
    FIGS[m.group(1)] = str(i)
order = []
for m in re.finditer(r"\\cite\{([^}]*)\}", main):
    for k in m.group(1).split(","):
        if k.strip() not in order:
            order.append(k.strip())
CITE_NUM.update({k: i + 1 for i, k in enumerate(order)})
refs = (HERE / "references_ieee.txt").read_text().strip().split("\n")
assert len(refs) == len(order), (len(refs), len(order))

# ── front matter ─────────────────────────────────────────────────────────────
p = add(clone("title")); set_runs(p, [(title, {})])
AFF = "School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai 600127, India"
for nm in ("HARSHA VARDAN M SAKAMURI", "ROHIT MICHAEL RAJ", "VALARMATHI P."):
    p = add(clone("authors")); set_runs(p, [(nm, {})])
    p = add(clone("affil")); set_runs(p, [(AFF, {})])
p = add(clone("abstract"))
set_runs(p, [("Abstract", dict(bold=True, italic=True)), ("\u2014", dict(bold=True))] + [(t, dict(f, bold=True)) for t, f in abstract])
add(clone("foot"))
for text in [
    "Manuscript received XXXXX 00, 0000; revised XXXXX 00, 0000; accepted XXXXX 00, 0000.",
    "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.",
    "(Corresponding author: Valarmathi P.)",
    "Valarmathi P. is with the School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai 600127, India (e-mail: valarmathi.sudhakar@vit.ac.in). Harsha Vardan M Sakamuri and Rohit Michael Raj are with the same school.",
    "The code, the result files and the source of this article are at https://github.com/Haise-727/gmat-pred.",
]:
    p = add(clone("history")); set_runs(p, [(text, {})])
p = add(clone("abstract"))
ppr = p.find(W + "pPr")
ind = ppr.find(W + "ind")
if ind is None:
    ind = etree.SubElement(ppr, W + "ind")
ind.set(W + "firstLine", "0")
sp = ppr.find(W + "spacing")
if sp is not None:
    ppr.remove(sp)
set_runs(p, [("Index Terms", dict(bold=True, italic=True)), ("\u2014" + keywords, dict(bold=True))])

# ── column layout helpers ────────────────────────────────────────────────────
def sect_variant(cols):
    s = copy.deepcopy(sect_main)
    for ref in [c for c in s if c.tag.endswith("Reference")]:
        s.remove(ref)
    for t in s.findall(W + "titlePg"):
        s.remove(t)
    t = s.find(W + "type")
    if t is None:
        t = etree.Element(W + "type"); s.insert(0, t)
    t.set(W + "val", "continuous")
    c = s.find(W + "cols")
    if cols == 1:
        for a in list(c.attrib):
            if a.endswith("}num"):
                del c.attrib[a]
    return s


first_break = [True]


def with_sect(p, kind):
    pPr = p.find(W + "pPr")
    if pPr is None:
        pPr = etree.Element(W + "pPr"); p.insert(0, pPr)
    if kind == "main":
        s = copy.deepcopy(sect_main)            # carries the header and footer references
    else:
        s = sect_variant(1 if kind == "one" else 2)
    pPr.append(s)


def empty_p():
    e = etree.Element(W + "p"); etree.SubElement(e, W + "pPr"); return e


def has_sect(p):
    pPr = p.find(W + "pPr")
    return pPr is not None and pPr.find(W + "sectPr") is not None


def wrap_wide(elements):
    first, last = elements[0], elements[-1]
    prev = first.getprevious()
    kind = "main" if first_break[0] else "two"
    first_break[0] = False
    if prev is not None and prev.tag == W + "p" and not has_sect(prev):
        with_sect(prev, kind)
    else:
        n = empty_p(); first.addprevious(n); with_sect(n, kind)
    if last.tag == W + "p" and not has_sect(last):
        with_sect(last, "one")
    else:
        n = empty_p(); last.addnext(n); with_sect(n, "one")


# ── tables, figures, equations ───────────────────────────────────────────────
def build_table(rows, widths, size=8):
    t = copy.deepcopy(T["table"])
    strip_ids(t)
    for tr in t.findall(W + "tr"):
        t.remove(tr)
    grid = t.find(W + "tblGrid")
    for g in list(grid):
        grid.remove(g)
    for w in widths:
        etree.SubElement(grid, W + "gridCol").set(W + "w", str(w))
    tw = t.find(W + "tblPr").find(W + "tblW")
    tw.set(W + "w", str(sum(widths))); tw.set(W + "type", "dxa")
    for ri, row in enumerate(rows):
        tr = etree.SubElement(t, W + "tr")
        col = 0
        for cell in row:
            text, span, align = cell["text"], cell.get("span", 1), cell.get("align", "left")
            tc = etree.SubElement(tr, W + "tc")
            tcpr = etree.SubElement(tc, W + "tcPr")
            etree.SubElement(tcpr, W + "tcW").set(W + "w", str(sum(widths[col:col + span])))
            if span > 1:
                etree.SubElement(tcpr, W + "gridSpan").set(W + "val", str(span))
            col += span
            p = etree.SubElement(tc, W + "p")
            ppr = etree.SubElement(p, W + "pPr")
            etree.SubElement(ppr, W + "pStyle").set(W + "val", "Para")
            if ri < len(rows) - 1:
                etree.SubElement(ppr, W + "keepNext")          # keep the table in one piece
            etree.SubElement(ppr, W + "ind").set(W + "firstLine", "0")
            sp = etree.SubElement(ppr, W + "spacing"); sp.set(W + "after", "0"); sp.set(W + "line", "240"); sp.set(W + "lineRule", "auto")
            etree.SubElement(ppr, W + "jc").set(W + "val", "center" if (ri == 0 or align == "center") else "left")
            for tx, f in inline(text):
                p.append(mkrun(tx, **dict(f, bold=f.get("bold", False) or ri == 0, size=size)))
    return t


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
            if m:
                cells.append(dict(text=m.group(2), span=int(m.group(1)), align="center"))
            else:
                cells.append(dict(text=c, align="left"))
        rows.append(cells)
    return rows


def col_widths(rows, total, size=8):
    n = max(sum(c.get("span", 1) for c in r) for r in rows)
    weight = [1.0] * n
    longest = [1] * n
    for r in rows:
        col = 0
        for c in r:
            txt = re.sub(r"[$\\{}]", "", c["text"])
            if c.get("span", 1) == 1:
                weight[col] = max(weight[col], min(len(txt), 40) ** 0.7)
                longest[col] = max(longest[col], max((len(w) for w in txt.split()), default=1))
            col += c.get("span", 1)
    per_char = size * 0.52 * 20            # twips per character
    minw = [int(per_char * L + 230) for L in longest]
    if sum(minw) > total:                  # not enough room: the caller shrinks the font
        return None
    extra = total - sum(minw)
    sw = sum(weight)
    return [minw[i] + int(extra * weight[i] / sw) for i in range(n)]


def center_numeric(rows):
    for r in rows[1:]:
        for c in r:
            if re.match(r"^[\d$.\-+e/ \\pm]+$", c["text"].strip()) or c["text"].strip() in ("none", "n/a"):
                c["align"] = "center"


def convert_equation(src, number):
    s = re.sub(r"\s+", " ", src).strip()
    s = s.replace("\\,", " ")
    if s.startswith("S ="):
        runs = [("S", dict(italic=True)), (" = 2 Std(", {}), ("p\u0302", dict(italic=True)), (")", {})]
    else:
        runs = [("D", dict(italic=True)), (" = Std(", {}), ("p\u0302", dict(italic=True)), (") / (Std(", {}),
                ("p\u0302", dict(italic=True)), ("healthy", dict(sub=True)), (") + ", {}), ("\u03b5", dict(italic=True)), (")", {})]
    p = clone("formula")
    set_runs(p, [("\t", {})] + runs + [(f"\t({number})", {})])
    return p


# ── body ─────────────────────────────────────────────────────────────────────
pos = 0
eq_no = 0
wide_pending = []
SCAN = re.compile(r"\\section\{([^}]*)\}|\\subsection\{([^}]*)\}|\\begin\{(equation|itemize|table\*?|figure\*?)\}", re.S)
text = main


def para_from(chunk):
    chunk = chunk.strip()
    if not chunk:
        return
    p = add(clone("para"))
    # a paragraph that continues straight after a displayed equation has no indent
    set_runs(p, inline(chunk))
    return p


while pos < len(text):
    m = SCAN.search(text, pos)
    if not m:
        for chunk in re.split(r"\n\s*\n", text[pos:]):
            para_from(chunk)
        break
    for chunk in re.split(r"\n\s*\n", text[pos:m.start()]):
        para_from(chunk)
    if m.group(1) is not None:
        p = add(clone("h1")); set_runs(p, [(m.group(1), {})]); pos = m.end()
        lab = re.match(r"\s*\\label\{[^}]*\}", text[pos:]);
        if lab: pos += lab.end()
    elif m.group(2) is not None:
        p = add(clone("h2")); set_runs(p, [(m.group(2), {})]); pos = m.end()
    else:
        env = m.group(3)
        end = text.index("\\end{" + env + "}", m.end())
        block = text[m.end():end]
        pos = end + len("\\end{" + env + "}")
        if env == "equation":
            eq_no += 1
            add(convert_equation(block, eq_no))
        elif env == "itemize":
            for item in re.split(r"\\item\s+", block)[1:]:
                p = add(clone("bullet")); set_runs(p, inline(item))
        elif env.startswith("table"):
            cap = re.search(r"\\caption\{(.*?)\}\s*\\label\{([^}]*)\}", block, re.S)
            number = TABS[cap.group(2)]
            c = add(clone("tabcap"))
            etree.SubElement(c.find(W + "pPr"), W + "keepNext")
            set_runs(c, [("TABLE " + number, {}), ("\n", {})] + inline(cap.group(1), dict(nobold=True)))
            for r_ in c.findall(W + "r"):
                if r_.find(W + "t") is not None and r_.find(W + "t").text == "\n":
                    r_.remove(r_.find(W + "t")); etree.SubElement(r_, W + "br")
            rows = parse_tabular(block)
            center_numeric(rows)
            ncol = max(sum(x.get("span", 1) for x in r) for r in rows)
            wide = env.endswith("*") or ncol >= 6
            total = 9400 if wide else 4700
            size = 8
            widths = col_widths(rows, total, size)
            if widths is None:
                size = 7
                widths = col_widths(rows, total, size) or [total // ncol] * ncol
            tbl = add(build_table(rows, widths, size))
            if wide:
                wide_pending.append([c, tbl])
        else:   # figure
            cap = re.search(r"\\caption\{(.*?)\}\s*\\label\{([^}]*)\}", block, re.S)
            number = FIGS[cap.group(2)]
            png = re.search(r"\\includegraphics\[[^\]]*\]\{([^}]*)\}", block).group(1)
            wide = env.endswith("*")
            ip = add(clone("image"))
            for c_ in list(ip):
                if c_.tag != W + "pPr":
                    ip.remove(c_)
            Paragraph(ip, d._body).add_run().add_picture(str(HERE / png), width=Inches(6.2 if wide else 3.2))
            fc = add(clone("figcap"))
            set_runs(fc, [("Fig. " + number, {}), ("\u2003", {})] + inline(cap.group(1)))
            if wide:
                wide_pending.append([ip, fc])

# ── acknowledgment, references, biographies ─────────────────────────────────
p = add(clone("h1")); set_runs(p, [("ACKNOWLEDGMENT", {})])
numpr = etree.SubElement(p.find(W + "pPr"), W + "numPr")
etree.SubElement(numpr, W + "numId").set(W + "val", "0")
p = add(clone("para")); set_runs(p, inline(ack))

p = add(clone("refhead"))
for i, ref in enumerate(refs, 1):
    e = add(clone("bib"))
    ref = ref.replace('"', "\u201c", 1).replace('"', "\u201d", 1)          # curly quotes around the title
    runs = [(f"[{i}]\t", {})]
    m = re.match(r"(.*?\u201d)\s*(.*)$", ref)
    if m:
        authors, rest = m.group(1), m.group(2)
        runs.append((authors + " ", {}))
        cm = re.match(r"((?:in )?)(.*?)(?=, vol\.|, pp\.|, (?:19|20)\d\d|\. doi|, doi|,? arXiv:|$)(.*)$", rest)
        if cm:
            runs += [(cm.group(1), {}), (cm.group(2), dict(italic=True)), (cm.group(3), {})]
        else:
            runs.append((rest, {}))
    else:
        runs.append((ref, {}))
    set_runs(e, runs)

for nm, txt in bios:
    p = add(clone("bio"))
    rr = p.findall(W + "r")
    name_rpr = copy.deepcopy(rr[0].find(W + "rPr")); body_rpr = copy.deepcopy(rr[1].find(W + "rPr"))
    for r_ in rr:
        p.remove(r_)
    a = etree.SubElement(p, W + "r"); a.append(copy.deepcopy(name_rpr))
    t = etree.SubElement(a, W + "t"); t.text = nm.upper(); t.set(XML + "space", "preserve")
    b = etree.SubElement(p, W + "r"); b.append(copy.deepcopy(body_rpr))
    t = etree.SubElement(b, W + "t"); t.text = " " + re.sub(r"\s+", " ", txt); t.set(XML + "space", "preserve")

# wide blocks go in single-column sections
for block in wide_pending:
    wrap_wide(block)

# ── footers ──────────────────────────────────────────────────────────────────
SHORT = "SAKAMURI ET AL.: DETECTING PREDICTION COLLAPSE CAUSED BY POOLED FEATURE NORMALIZATION"
for part in d.part.package.iter_parts():
    if not re.search(r"/word/footer\d*\.xml$", str(part.partname)):
        continue
    root = part._element
    for p_ in root.iter(W + "p"):
        tnodes = list(p_.iter(W + "t"))
        whole = "".join(t.text or "" for t in tnodes)
        new = whole.replace("AUTHOR ET AL.: SHORT ARTICLE TITLE", SHORT).replace("2022", "2026")
        if new != whole and tnodes:
            tnodes[0].text = new
            for t in tnodes[1:]:
                t.text = ""

d.save(str(OUT))
print("saved", OUT)
