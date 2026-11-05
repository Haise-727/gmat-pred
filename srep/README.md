# Single column version (Springer Nature, Scientific Reports style)

Made after the TAES desk rejection, following the guide's sample paper
(Scientific Reports, doi 10.1038/s41598-026-74017-1), and revised on 5 Nov 2026 after
the internal review (comments in `suggestions-nov5.docx`, not kept in the repo).

- `manuscript.tex`: the text. Some tables are pulled from `eaai/manuscript.tex` by label
  (with a shorter caption after a `|`), and three tables are generated from the data, so
  no number is typed twice.
- `make_srep_docx.py`: builds `OrbitGuard_SciRep.docx` in the repository root
  (A4, Times New Roman 12 pt, single column, citations as [1], Nature style references,
  numbered equations as real Word equations, one algorithm box).
  The PDF next to it is the same file converted with LibreOffice.
- `omml.py`: turns the LaTeX equations into Word (OMML) equations.
- `pipeline_figure.py`, `data_figure.py`, `modes_figure.py`: draw Figures 1, 2 and 3.
- `fig2.png` to `fig6.png`: the result figures of the main paper, redrawn at 600 dpi
  with American spelling from the same result files (same content as `eaai/fig2.png`
  to `eaai/fig6.png`, where `fig5.png` is the seeds figure).
- `references.bib`: the bibliography. The literature review covers learned models for
  transfer cost and feasibility, neural guidance and control, orbit prediction and
  uncertainty propagation, and screening in space operations. Every entry was checked
  on Crossref or arXiv.
- New results used here: `reports/significance.json` (`src/ml/significance.py`) and
  `reports/diagnostic_protocol.json` (`src/ml/diagnostic_protocol.py`).
