"""
A small LaTeX to Office Math (OMML) converter for the equations in srep/manuscript.tex.

Only the subset the paper uses is handled: letters, numbers, Greek letters and common
symbols, sub and superscripts, \\frac, \\binom, \\sqrt, \\sum, \\hat, \\bar, \\tilde, \\left( \\right),
\\mathrm, \\text, \\operatorname and function names such as \\log or \\max. The result is a
<m:oMath> element that Word and LibreOffice show as a real equation.

    from omml import omath
    paragraph._p.append(omath(r"S = 2 s_g", size=12))
"""

import re
from xml.sax.saxutils import escape

from docx.oxml import parse_xml

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

SYMBOLS = {
    "times": "×", "pm": "±", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥",
    "ne": "≠", "neq": "≠", "approx": "≈", "in": "∈", "notin": "∉", "mid": "|", "cdot": "·",
    "ldots": "…", "dots": "…", "infty": "∞", "rightarrow": "→", "to": "→", "leftarrow": "←",
    "gets": "←", "lvert": "|", "rvert": "|", "vert": "|", "lfloor": "⌊", "rfloor": "⌋",
    "{": "{", "}": "}", "%": "%", "#": "#", "&": "&", "_": "_", "cup": "∪", "cap": "∩",
    "subset": "⊂", "forall": "∀", "exists": "∃", "neg": "¬", "land": "∧", "lor": "∨",
    "prime": "′", "star": "⋆", "propto": "∝", "equiv": "≡", "sim": "∼", "Leftarrow": "⇐",
    "Rightarrow": "⇒", "emptyset": "∅", "ell": "\u2113", "lceil": "\u2308", "rceil": "\u2309",
}
GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "varepsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "kappa": "κ", "lambda": "λ", "mu": "μ",
    "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ",
    "phi": "φ", "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Sigma": "Σ", "Phi": "Φ",
    "Omega": "Ω",
}
FUNCS = {"log", "ln", "exp", "max", "min", "arg", "sup", "inf", "det", "Pr", "sin", "cos", "tanh", "median", "softmax"}
NARY = {"sum": "∑", "prod": "∏", "int": "∫"}
ACCENT = {"hat": "̂", "tilde": "̃", "dot": "̇", "vec": "⃗"}
SPACES = {",": " ", ";": " ", ":": " ", "quad": " ", "qquad": "  ", " ": " ", "!": ""}

TOKEN = re.compile(r"\\[A-Za-z]+|\\.|[{}^_]|\s+|.")


class _Parser:
    def __init__(self, src):
        self.t = [t for t in TOKEN.findall(src)]
        self.i = 0

    def peek(self):
        while self.i < len(self.t) and self.t[self.i].isspace():
            self.i += 1
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def raw_group(self):
        """Text inside the next {...}, kept as written (for \\text and \\mathrm)."""
        assert self.take() == "{"
        depth, out = 1, []
        while self.i < len(self.t):
            tok = self.t[self.i]; self.i += 1
            if tok == "{":
                depth += 1
            elif tok == "}":
                depth -= 1
                if depth == 0:
                    break
            out.append(tok)
        return "".join(out).replace("\\_", "_").replace("\\%", "%").replace("\\,", " ").replace("\\ ", " ")

    def seq(self, stop=None):
        nodes = []
        while True:
            tok = self.peek()
            if tok is None or tok == stop or (stop == "}" and tok == "}"):
                return nodes
            if tok == "\\right" and stop == "\\right":
                return nodes
            node = self.atom()
            if node is not None:
                nodes.append(self.scripts(node))

    def scripts(self, base):
        sub = sup = None
        while self.peek() in ("_", "^"):
            kind = self.take()
            arg = self.atom()
            if kind == "_":
                sub = arg
            else:
                sup = arg
        if base[0] == "nary":
            return ("nary", base[1], sub, sup, self.scripts(self.atom()))
        if sub is not None and sup is not None:
            return ("subsup", base, sub, sup)
        if sub is not None:
            return ("sub", base, sub)
        if sup is not None:
            return ("sup", base, sup)
        return base

    def atom(self):
        tok = self.take()
        if tok is None:
            return ("grp", [])
        if tok == "{":
            inner = self.seq("}")
            self.take()
            return ("grp", inner)
        if tok.startswith("\\") and len(tok) > 1:
            name = tok[1:]
            if name == "frac":
                return ("frac", self.atom(), self.atom())
            if name == "binom":
                return ("binom", self.atom(), self.atom())
            if name == "mathcal":
                txt = self.raw_group()
                return ("r", {"L": "\u2112", "F": "\u2131", "N": "\U0001d4a9"}.get(txt, txt), False)
            if name == "sqrt":
                return ("rad", self.atom())
            if name in ("left", "big", "Big", "bigl", "bigr"):
                delim = self.take()
                delim = SYMBOLS.get(delim[1:], delim[1:]) if delim.startswith("\\") else delim
                if name != "left":
                    return ("r", delim, True)
                inner = self.seq("\\right")
                self.take()
                close = self.take()
                close = SYMBOLS.get(close[1:], close[1:]) if close.startswith("\\") else close
                return ("d", "" if delim == "." else delim, "" if close == "." else close, inner)
            if name in ACCENT:
                return ("acc", ACCENT[name], self.atom())
            if name in ("bar", "overline"):
                return ("bar", self.atom())
            if name in ("mathrm", "text", "operatorname", "textrm"):
                return ("r", self.raw_group(), True)
            if name in ("mathbf", "boldsymbol"):
                return ("b", self.raw_group())
            if name == "mathbb":
                txt = self.raw_group()
                return ("r", {"1": "\U0001d7d9", "R": "ℝ", "E": "\U0001d53c"}.get(txt, txt), True)
            if name in ("mathit",):
                return ("r", self.raw_group(), False)
            if name in NARY:
                return ("nary", NARY[name])
            if name in GREEK:
                return ("r", GREEK[name], name[0].isupper())
            if name in FUNCS:
                return ("r", name, True)
            if name in SYMBOLS:
                return ("r", SYMBOLS[name], True)
            if name in SPACES:
                return ("r", SPACES[name], True)
            return ("r", name, True)
        if tok.startswith("\\"):
            ch = tok[1:]
            return ("r", SPACES.get(ch, SYMBOLS.get(ch, ch)), True)
        if tok in ("}",):
            return None
        if tok.isalpha():
            return ("r", tok, False)
        if tok == "-":
            return ("r", "−", True)
        if tok == "'":
            return ("r", "′", True)
        return ("r", tok, True)


def _merge(nodes):
    out = []
    for n in nodes:
        if out and n[0] == "r" and out[-1][0] == "r" and n[2] and out[-1][2]:
            out[-1] = ("r", out[-1][1] + n[1], True)
        else:
            out.append(n)
    return out


def _xml(n, rpr):
    kind = n[0]
    if kind == "grp":
        return "".join(_xml(c, rpr) for c in _merge(n[1]))
    if kind in ("r", "b"):
        plain = kind == "b" or n[2]
        # upright text: words get m:nor (normal text, which LibreOffice also keeps upright), symbols m:sty p
        if not plain:
            sty = ""
        elif kind == "b":
            sty = '<m:rPr><m:sty m:val="b"/></m:rPr>'
        elif any(ch.isalpha() for ch in n[1]) and len(n[1]) > 1:
            sty = "<m:rPr><m:nor/></m:rPr>"
        else:
            sty = '<m:rPr><m:sty m:val="p"/></m:rPr>'

        return f'<m:r>{sty}{rpr}<m:t xml:space="preserve">{escape(n[1])}</m:t></m:r>'
    if kind == "frac":
        return f"<m:f><m:num>{_xml(n[1], rpr)}</m:num><m:den>{_xml(n[2], rpr)}</m:den></m:f>"
    if kind == "binom":
        return ('<m:d><m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr><m:e><m:f><m:fPr><m:type m:val="noBar"/></m:fPr>'
                f"<m:num>{_xml(n[1], rpr)}</m:num><m:den>{_xml(n[2], rpr)}</m:den></m:f></m:e></m:d>")
    if kind == "rad":
        return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{_xml(n[1], rpr)}</m:e></m:rad>'
    if kind == "acc":
        return f'<m:acc><m:accPr><m:chr m:val="{n[1]}"/></m:accPr><m:e>{_xml(n[2], rpr)}</m:e></m:acc>'
    if kind == "bar":
        return f'<m:bar><m:barPr><m:pos m:val="top"/></m:barPr><m:e>{_xml(n[1], rpr)}</m:e></m:bar>'
    if kind == "d":
        return (f'<m:d><m:dPr><m:begChr m:val="{escape(n[1])}"/><m:endChr m:val="{escape(n[2])}"/></m:dPr>'
                f"<m:e>{_xml(('grp', n[3]), rpr)}</m:e></m:d>")
    if kind == "sub":
        return f"<m:sSub><m:e>{_xml(n[1], rpr)}</m:e><m:sub>{_xml(n[2], rpr)}</m:sub></m:sSub>"
    if kind == "sup":
        return f"<m:sSup><m:e>{_xml(n[1], rpr)}</m:e><m:sup>{_xml(n[2], rpr)}</m:sup></m:sSup>"
    if kind == "subsup":
        return (f"<m:sSubSup><m:e>{_xml(n[1], rpr)}</m:e><m:sub>{_xml(n[2], rpr)}</m:sub>"
                f"<m:sup>{_xml(n[3], rpr)}</m:sup></m:sSubSup>")
    if kind == "nary":
        hide = ('<m:subHide m:val="1"/>' if n[2] is None else "") + ('<m:supHide m:val="1"/>' if n[3] is None else "")
        sub = _xml(n[2], rpr) if n[2] is not None else ""
        sup = _xml(n[3], rpr) if n[3] is not None else ""
        return (f'<m:nary><m:naryPr><m:chr m:val="{n[1]}"/><m:limLoc m:val="undOvr"/>{hide}</m:naryPr>'
                f"<m:sub>{sub}</m:sub><m:sup>{sup}</m:sup><m:e>{_xml(n[4], rpr)}</m:e></m:nary>")
    raise ValueError(n)


def omath(latex, size=None):
    """The <m:oMath> element for one LaTeX formula."""
    sz = f'<w:sz w:val="{int(size * 2)}"/><w:szCs w:val="{int(size * 2)}"/>' if size else ""
    rpr = f'<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>{sz}</w:rPr>'
    body = _xml(("grp", _Parser(latex).seq()), rpr)
    return parse_xml(f'<m:oMath xmlns:m="{M_NS}" xmlns:w="{W_NS}">{body}</m:oMath>')
