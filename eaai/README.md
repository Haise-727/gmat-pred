# EAAI LaTeX conversion of Gmat_Pred_Research.docx

Source of truth: `_source_extract/Gmat_Pred_Research.docx` (copy of the original Word file).

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

Elsevier Editorial Manager cannot use subfolders. For **double-anonymized review** upload:

- `title_page.tex` and `title_page.pdf`
- `manuscript_anonymous.tex` and `manuscript_anonymous.pdf`
- `references.bib`
- `elsarticle-harv.bst`
- `elsarticle.cls` (if the journal system does not already provide it)
- `fig1.png` ... `fig7.png`

`manuscript.tex` / `manuscript.pdf` is the complete identifying version for you, not the review file.

## Author input still required

See `CONTENT_PRESERVATION_REPORT.md`. Highlights, graphical abstract, affiliations, corresponding-author email, competing-interest, CRediT, and funding were not in the Word file and were not invented.
