# EAAI LaTeX version of the paper

Source of truth for the text: `OrbitGuard_paper.docx` at the repository root.
The LaTeX files carry the same text.

## Compile

From this folder, in PowerShell:

```powershell
.\compile.ps1
```

or:

```
pdflatex manuscript.tex
bibtex manuscript
pdflatex manuscript.tex
pdflatex manuscript.tex
```

Output: `manuscript.pdf`

## Submission files (keep in one folder)

Elsevier Editorial Manager cannot use subfolders. For double anonymised review
upload:

- `title_page.tex` and `title_page.pdf`
- `manuscript_anonymous.tex` and `manuscript_anonymous.pdf`
- `highlights.docx`, as a separate file
- `references.bib`
- `elsarticle-harv.bst`
- `elsarticle.cls` (if the journal system does not already provide it)
- `fig1.png` to `fig7.png`

`manuscript.tex` and `manuscript.pdf` are the full version with author names.
They are for the authors, not the review file.

## What is still open

See `CONTENT_PRESERVATION_REPORT.md`. In short: the graphical abstract is
optional and has not been made, the competing interest, CRediT and funding
statements need the authors' confirmation, and the standard deviation used in
Table III is waiting on a decision.
