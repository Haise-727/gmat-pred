# Single column version (Springer Nature, Scientific Reports style)

Made after the TAES desk rejection, following the guide's sample paper
(Scientific Reports, doi 10.1038/s41598-026-74017-1).

- `manuscript.tex`: the text. Tables and figures shared with the main paper are pulled
  from `eaai/manuscript.tex` by label, and three tables are generated from the data, so
  no number is typed twice.
- `make_srep_docx.py`: builds `OrbitGuard_SciRep.docx` in the repository root
  (A4, Times New Roman 12 pt, single column, Nature style references).
  The PDF next to it is the same file converted with LibreOffice.
- `pipeline_figure.py`: draws Figure 1.
- `references.bib`: the main bibliography with the three IEEE TAES papers replaced by
  Springer papers (Peng and Bai 2020, Balducci et al. 2017, Herrmann et al. 2024).
- New results used here: `reports/significance.json` (`src/ml/significance.py`) and
  `reports/diagnostic_protocol.json` (`src/ml/diagnostic_protocol.py`).
