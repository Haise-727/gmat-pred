# Content-preservation report

**Source of truth:** `c:\Users\rohit michael\Downloads\Gmat_Pred_Research.docx` (copied to `_source_extract/Gmat_Pred_Research.docx`). No external draft, GitHub tree, or inferred paper was used to replace wording, numbers, table cells, captions, or references.

**Conversion target:** Engineering Applications of Artificial Intelligence (EAAI), using the official Elsevier `elsarticle` class in single-column preprint form with Harvard / author–year citations (`elsarticle-harv.bst`). EAAI desk-rejects papers that are not single-column.

**Compiled output:** `manuscript.pdf` (24 pages).

---

## Validation summary

| Item | Original Word | LaTeX | Status |
|---|---|---|---|
| Title | Present | Present, identical | Preserved |
| Authors | 3 names, no affiliations | Same 3 names | Preserved; affiliations are placeholders |
| Abstract | 1 paragraph | Same paragraph | Preserved (271 words; EAAI limit is 250) |
| Keywords / Index Terms | 6 terms | Same 6 terms | Preserved |
| Headings | I–X | Sections 1–10 with the same titles | Formatting only |
| Body paragraphs | All non-empty body paragraphs | Present | Preserved |
| Tables | 5 | 5, same cells | Preserved |
| Figures | 7 PNG images + 7 captions | `fig1.png`–`fig7.png` + same captions | Preserved |
| Display equations | None in the Word file | None added | n/a |
| References | [1]–[43] | 43 BibTeX entries | Preserved; citation *style* converted to Harvard |
| New research sentences | — | None | No research text invented |

Empty Word paragraphs (spacing) were dropped. That is layout, not content.

---

## Formatting-only changes (allowed)

1. **Document class.** IEEE-like Word layout → `\documentclass[preprint,12pt,authoryear]{elsarticle}` with `\journal{Engineering Applications of Artificial Intelligence}`.
2. **Abstract label.** Word `Abstract—` prefix removed; text placed in `\begin{abstract}...\end{abstract}`.
3. **Keywords label.** Word `Index Terms—` → Elsevier `\begin{keyword}` with `\sep`.
4. **Section numbering.** Roman `I.`–`X.` → Elsevier arabic 1–10. Heading words are unchanged. In-text “Section VI”, “Section VII”, “Section V” now use `\ref` and will print as Section 6, 7, and 5.
5. **Table numbering.** `TABLE I`–`TABLE V` → `Table 1`–`Table 5` via `\caption`. Caption sentences after those labels are unchanged.
6. **Figure numbering.** `Fig. 1.`–`Fig. 7.` prefixes removed from captions because LaTeX supplies `Fig. n`. Caption sentences are unchanged.
7. **Citations.** Numbered `[1]`, `[2, 3]`, … converted to `\citep{...}` so EAAI Harvard style prints as `(Author, year)`. Sentence wording around those markers is unchanged. Two 2019 Izzo papers are disambiguated by BibTeX as 2019a / 2019b, which Harvard requires.
8. **References.** IEEE numbered list → `references.bib` + `elsarticle-harv`. Titles, venues, years, volumes, pages, and DOIs were copied from the Word list. Author names written as “et al.” in Word were **not** expanded.
9. **Identifiers.** `dv_V`, `d_model`, `surface_impact`, file paths, and similar tokens are in `\texttt{...}` with escaped underscores. The tokens are unchanged.
10. **Percent signs.** `40%`, `64.5%`, etc. escaped as `\%`.
11. **Table I header row.** The Word header was `Target | sig | AUC | std` repeated three times. A formatting-only group row `per-timestep | global | grouped` was added so the three repeated `(sig, AUC, std)` blocks remain readable. Those group names are the three conditions already named in Section III. **All numeric cells are identical to the Word table.**
12. **Table III.** `±` is in math mode (`$0.9998 \pm 0.0001$`). Values are unchanged.
13. **Limitations.** Five bullets kept as `\begin{itemize}`. The Word wrap “All four / agree on the result…” was rejoined into one bullet (it was one list item split across two Word paragraphs).
14. **Code listing.** The bash block is in `verbatim` (then `\scriptsize` so long lines fit). Commands, comments, and `Table I`–`Table V` / `Fig. 2` comments inside the listing were left as in the Word file.
15. **Quotes.** Word straight quotes around short phrases such as `collapse` and `test` were converted to LaTeX quotes. Wording is unchanged.
16. **Figure files.** Extracted from `word/media/image1.png`–`image7.png` and renamed `fig1.png`–`fig7.png` in document order.

---

## Remaining items (left for later, as requested)

These were **not** written into the paper:

- **Highlights.** 3–5 bullets, each at most 85 characters including spaces. Encouraged by EAAI, not drafted.
- **Graphical abstract.** A single wide image that summarises the paper for the journal website (about 531 × 1328 pixels). Encouraged, not drafted.
- **Abstract length.** Still 271 words; EAAI asks for ≤250.
- **Keywords.** Left as the original six Index Terms. EAAI prefers avoiding multi-word keywords.
- **Inspec classification codes.** Up to 6; none supplied.
- **ORCIDs.** None supplied.

Filled later from author input: corresponding email `valarmathi.sudhakar@vit.ac.in`; address Vandalur--Kelambakkam Road, Melakottaiyur, Chennai 600127, Tamil Nadu, India.

## Double-anonymized split

- `title_page.tex` / `title_page.pdf` — authors, affiliation, corresponding author, competing interest, CRediT, funding.
- `manuscript_anonymous.tex` / `manuscript_anonymous.pdf` — review file; authors and GitHub URL removed.
- `manuscript.tex` / `manuscript.pdf` — complete author-identifying version.

---

## Journal checks reported, not auto-fixed

- **Abstract length.** The original abstract is **271 words**. EAAI asks for ≤250. It was **not** shortened.
- **Double-anonymized review.** EAAI wants a separate title page (authors, affiliations, acknowledgements, competing interest, corresponding-author address/email) and an anonymized manuscript. The compiled `manuscript.tex` currently includes the three author names so the complete paper can be checked. Before Editorial Manager upload, copy author details to a title-page file and strip them from the review PDF.
- **Keywords.** EAAI prefers avoiding multi-word keywords; the original six Index Terms were kept unchanged.
- **BibTeX empty-pages warnings.** Nine conference/incollection entries have no page numbers because the Word file did not give pages. Pages were not invented.

---

## Typographical / LaTeX-only corrections

No research wording was corrected. The only mechanical escapes required for compilation were:

- `_` → `\_` inside `\texttt` and file names
- `%` → `\%` in running text
- `>` in “AUC of >0.95” → `$>$0.95`
- Accented bibliography names encoded as LaTeX accents (`W{\"a}ldchen`, `M{\"u}ller`, `S{\"o}derstr{\"o}m`, `M{\"a}rtens`, `S{\'a}nchez-S{\'a}nchez`, `Doll{\'a}r`, `Rodr{\'i}guez-Fern{\'a}ndez`)

---

## What was explicitly not done

- No new paragraphs, literature, explanations, or conclusions.
- No grammar or style rewrite.
- No invented affiliations, emails, ORCIDs, DOIs, co-authors, results, or data.
- No change to experimental numbers, table cells, figure pixels, or captions.
- “et al.” reference author lists were not expanded from the web.
- The GitHub repository named in the paper was not used as an alternate manuscript source.

---

## How to rebuild

```powershell
.\compile.ps1
```

Main artefacts: `manuscript.tex`, `references.bib`, `elsarticle-harv.bst`, `fig1.png`–`fig7.png`, `manuscript.pdf`.
