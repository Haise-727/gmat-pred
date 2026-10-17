"""
Build taes/manuscript_taes.tex from eaai/manuscript.tex.

The scientific text is copied as it is. Only the format changes:
  * the official IEEEtaes class and bibliography style
  * numbered citations in place of author-year
  * TAES front matter (title, authors, affiliation, abstract, index terms)
  * section headings in capitals, as the TAES template does
  * the generative AI disclosure moves to the Acknowledgment
  * biographies after the references

    python taes/make_taes.py
"""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE.parent / "eaai" / "manuscript.tex").read_text()

title = "Detecting Prediction Collapse Caused by Pooled Feature Normalization in Space-Trajectory Screening"
abstract = re.search(r"\\begin\{abstract\}\n(.*?)\n\\end\{abstract\}", src, re.S).group(1).strip()
body = src[src.index("\\section{Introduction}"):src.index("\\bibliographystyle")]

# keep the body only up to the unnumbered statements; they are handled below
body = body[:body.index("\\section*{Declaration of competing interest}")]

a = body.index("\\section{Code and Data Availability}")
code_new = ("\\section{Code and Data Availability}\n\\label{sec:code}\n\n"
            "All the scripts for the experiments, the JSON artifacts that each number is read from, the code for the figures "
            "and the source of this document are at \\url{https://github.com/Haise-727/gmat-pred}.\n\n"
            "The JSON creates the tables and figures in this manuscript and not the other way round. "
            "No number was typed into the manuscript by hand.\n")
body = body[:a] + code_new

body = body.replace("\\citep", "\\cite")
body = re.sub(r"\\section\{([^}]*)\}", lambda m: "\\section{" + m.group(1).upper() + "}", body)

# wide items go across both columns
body = body.replace("\\begin{table}[t]\n\\centering\n\\caption{Normalisation ablation.", "\\begin{table*}[t]\n\\centering\n\\caption{Normalisation ablation.")
a = body.index("\\caption{Normalisation ablation.")
b = body.index("\\end{table}", a)
body = body[:b] + "\\end{table*}" + body[b + len("\\end{table}"):]
body = body.replace("\\resizebox{\\linewidth}{!}{%", "\\resizebox{\\textwidth}{!}{%")

for fig in ("fig1.png", "fig2.png", "fig6.png"):
    m = re.search(r"\\begin\{figure\}\[t\]\n\\centering\n\\includegraphics\[width=\\linewidth\]\{" + fig + r"\}.*?\\end\{figure\}", body, re.S)
    blk = m.group(0)
    new = blk.replace("\\begin{figure}[t]", "\\begin{figure*}[t]").replace("\\end{figure}", "\\end{figure*}")
    new = new.replace("width=\\linewidth", "width=0.8\\textwidth")
    body = body.replace(blk, new)

# the shell listing is too wide for a column: set it across both columns
m = re.search(r"\{\\scriptsize\n\\begin\{verbatim\}.*?\\end\{verbatim\}\n\}", body, re.S)
if m:
    body = body.replace(m.group(0), "\\begin{figure*}[!t]\n\\centering\n" + m.group(0) + "\n\\end{figure*}")

AMERICAN = [("NORMALISATION", "NORMALIZATION"), ("normalisations", "normalizations"), ("normalisation", "normalization"), ("Normalisation", "Normalization"),
            ("normalised", "normalized"), ("labelled", "labeled"), ("behaviour", "behavior"),
            ("initialisation", "initialization"), ("artefacts", "artifacts"), ("artefact", "artifact"),
            ("unmodelled", "unmodeled"), ("modelling", "modeling"), ("optimiser", "optimizer"),
            ("categorised", "categorized"), ("summarised", "summarized"), ("levelling", "leveling"),
            ("generalises", "generalizes"), ("standardisation", "standardization"),
            ("neighbourhood", "neighborhood"), ("towards", "toward"), ("whilst", "while")]


def americanise(text):
    """Spelling only. File names, commands and labels are left alone."""
    keep = re.compile(r"\\texttt\{[^}]*\}|\\cite\{[^}]*\}|\\ref\{[^}]*\}|\\label\{[^}]*\}|\\url\{[^}]*\}|\\begin\{verbatim\}.*?\\end\{verbatim\}", re.S)
    parts, last, out = [], 0, []
    for m in keep.finditer(text):
        out.append(("t", text[last:m.start()])); out.append(("k", m.group(0))); last = m.end()
    out.append(("t", text[last:]))
    res = []
    for kind, seg in out:
        if kind == "t":
            for o, n in AMERICAN:
                seg = seg.replace(o, n)
        res.append(seg)
    return "".join(res)


body = americanise(body)
abstract = americanise(abstract)

ai_text = (
    "AI use disclosure. During the preparation of this work the authors used Claude (Anthropic) "
    "to write and debug the experiment code, to draft the text of all sections, and to check the "
    "references and the numbers against the result files. The involvement of the tool was large in "
    "the code and in the first drafts of the text. The authors reviewed, edited and verified the "
    "content and take full responsibility for it."
)

tex = r"""\documentclass{IEEEtaes}

\usepackage{color,array,amsthm}
\usepackage{amsmath,amssymb}
\usepackage{booktabs,tabularx}
\usepackage{graphicx}
\usepackage{url}
\makeatletter
\def\verbatim@font{\fontfamily{pcr}\selectfont\footnotesize\frenchspacing\@noligs}
\makeatother

\jvol{XX}
\jnum{XX}
\jmonth{XXXXX}
\paper{1234567}
\pubyear{2026}
\doiinfo{TAES.2026.Doi Number}

\setcounter{page}{1}

\begin{document}

\title{""" + title + r"""}

\author{HARSHA VARDAN M SAKAMURI}
\affil{School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai 600127, India}

\author{ROHIT MICHAEL RAJ}
\affil{School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai 600127, India}

\author{VALARMATHI P.}
\affil{School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai 600127, India}

\receiveddate{Manuscript received XXXXX 00, 0000; revised XXXXX 00, 0000; accepted XXXXX 00, 0000.\\
This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.}

\corresp{{\itshape (Corresponding author: Valarmathi P.)}}

\authoraddress{Valarmathi P. is with the School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai 600127, India (e-mail: valarmathi.sudhakar@vit.ac.in). Harsha Vardan M Sakamuri and Rohit Michael Raj are with the same school.}

\supplementary{The code, the result files and the source of this article are at https://github.com/Haise-727/gmat-pred.}

\markboth{SAKAMURI \MakeLowercase{\textit{et al.}}}{DETECTING PREDICTION COLLAPSE CAUSED BY POOLED FEATURE NORMALIZATION}
\maketitle

\begin{abstract}""" + abstract + r"""\end{abstract}

\begin{IEEEkeywords}Feature normalization, model diagnostics, prediction spread, shortcut learning, simulation screening, trajectory analysis\end{IEEEkeywords}

""" + body + r"""
\section*{ACKNOWLEDGMENT}
""" + ai_text + r"""

\bibliographystyle{IEEEtaes}
\bibliography{references}

\begin{IEEEbiographynophoto}{Harsha Vardan M Sakamuri}
is pursuing the B.Tech. degree in Computer Science and Engineering (core) at the School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai, India, from 2024 to 2028. Their work centers on system administration and DevOps, and on automation using artificial intelligence and machine learning.
\end{IEEEbiographynophoto}

\begin{IEEEbiographynophoto}{Rohit Michael Raj}
is with the School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai, India. Their interests are artificial intelligence and machine learning, and they want to do research on problems that help industry.
\end{IEEEbiographynophoto}

\begin{IEEEbiographynophoto}{Valarmathi P.}
is with the School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Chennai, India. [Position, highest degree and where it was earned.] [Research interests.] [Selected publications or years of experience.]
\end{IEEEbiographynophoto}

\end{document}
"""
(HERE / "manuscript_taes.tex").write_text(tex)
print("wrote manuscript_taes.tex", len(tex.split()), "words")
