# Content preservation report

This file records how the LaTeX paper in this folder relates to the Word copy,
and which text changes were made after the first conversion.

**Source of truth for the text:** `OrbitGuard_paper.docx` at the repository root.
The LaTeX files carry the same text. If the two ever disagree, change the LaTeX
to match the Word file.

**Target journal:** Engineering Applications of Artificial Intelligence (EAAI).
Elsevier class `elsarticle`, single column preprint, Harvard author year
citations (`elsarticle-harv.bst`). EAAI sends back papers that are not single
column.

---

## Current state

| Item | State |
|---|---|
| Title | Same as the Word file |
| Authors | Three. The third author is Valarmathi P., the corresponding author |
| Affiliation and email | Filled in: SCOPE, Vellore Institute of Technology, Chennai. Email `valarmathi.sudhakar@vit.ac.in` |
| Abstract | 220 words (the journal says about 250). AUC and standard deviation are defined, and the AI contribution and the engineering application are stated |
| Keywords | The original six, unchanged |
| Sections | 1 to 11. Sections 6 and 7 are new (see the changes below). The rest keep the Word file's titles |
| Tables | 8. Every cell matches the files in `reports/`. In Table III the spread is the population standard deviation over the 5 seeds (divide by n) |
| Figures | 6 PNG files. Figures 1 to 5 have the original captions. Figure 6 is new |
| References | 44 BibTeX entries, every one cited |
| Declaration | The journal's generative AI declaration, above the references |
| Highlights | 5, in `highlights.docx` and `highlights.tex` |
| Graphical abstract | `graphical_abstract.tiff`, drawn by `graphical_abstract.py` from `reports/`. Optional for EAAI |

---

## Formatting changes from the first conversion

These change layout only, not wording.

1. **Document class.** The Word layout became `elsarticle` with `\journal{Engineering Applications of Artificial Intelligence}`.
2. **Abstract and keywords.** The `Abstract` and `Index Terms` labels were replaced by the Elsevier `abstract` and `keyword` environments.
3. **Numbering.** Roman section numbers became 1 to 10. Table and figure numbers are added by LaTeX, so the `TABLE I` and `Fig. 1.` prefixes were removed. Cross references such as "Section VI" use `\ref`.
4. **Citations.** Numbered citations became author year citations with `\citep`. Two 2019 Izzo papers appear as 2019a and 2019b, as Harvard style requires.
5. **References.** The numbered list became `references.bib`. Author lists written as "et al." in the Word file were not expanded.
6. **Identifiers.** Names such as `dv_V`, `d_model` and `surface_impact`, and file paths, are set in `\texttt` with escaped underscores.
7. **Table I.** A group row (`per-timestep`, `global`, `grouped`) was added above the three repeated blocks of `sig`, `AUC` and `std`, so they stay readable. The cells are unchanged.
8. **Limitations.** The five bullets are a `\begin{itemize}` list.
9. **Code listing.** The shell commands are in `verbatim`, in a smaller font so long lines fit.
10. **Figure files.** The images were taken from the Word file and named `fig1.png` to `fig5.png` in document order. `fig6.png` is new and is drawn by `new_results.py`.
11. **Escapes.** `_` and `%` are escaped, `>` in "AUC of >0.95" is in math mode, and accented author names use LaTeX accents.

---

## Text changes after the first conversion

These change what the paper says. Each one was checked against the files in
`reports/`.

| # | Where | Change | Why |
|---|---|---|---|
| 1 | Abstract | "The collapse is the same across the 5 seeds" became "The compression is the same across the 5 seeds, and the collapse occurs on 4 of them" | The squashing of the signal is the same on every seed. The collapse is not |
| 2 | Introduction, first sentence | Now says the compute is used on runs that were already sure to fail when they left the parking orbit | The old wording described the cost of a campaign wrongly |
| 3 | Related Work | "There is no article in this literature" became "We could not find an article in this literature" | Absence of an article cannot be shown, only that we did not find one |
| 4 | Related Work | The sentence about audio work was removed, with its reference (Salamon and Bello, 2017) | That paper is about a sound classifier and data augmentation. It says nothing about normalisation statistics. The list is now 42 entries |
| 5 | Section 4 | "a factor of 100" became "a factor of 23" | The measured reduction is 5.8 to 22.9 across the four targets |
| 6 | Section 4 | "one number per mission" became "one number for every mission" | The collapsed model gives the same number to every mission |
| 7 | Section 5 | "at most 0.0004" became "at most 0.0010" | The largest difference between seeds is 0.0010, on Mars |
| 8 | Limitations | "generic to astrodynamics" became "not specific to astrodynamics" | The mechanism is a variance ratio. It is not tied to astrodynamics |
| 9 | Conclusion | Two broken sentences repaired as the authors worded them | They were not complete sentences |
| 10 | Abstract | AUC and standard deviation defined at first use. A sentence stating the AI contribution and the engineering application was added. Four passages were cut or merged. 271 words became 242 | The journal asks for these, and for about 250 words |
| 11 | Before the references | The journal's generative AI declaration was added | Required by Elsevier |
| 12 | Authors | The third author is now Valarmathi P. | Author's request |
| 13 | Introduction | Added a short paragraph saying the contribution is how the failure hides and a check that finds it, not the fix. The three contributions now end with the second dataset. "Two failures and one bad result" became one failure | Reviewer comments from the mentor. The second failure was removed (see 15) |
| 14 | Related Work | Added ST-Norm and Deep Adaptive Input Normalization, and a sentence on how our question differs. The paragraph on class imbalance was removed, with six references (Buda, Lin, Cui, Dong, Sadr, Wu 2021) | Those references only supported the removed section |
| 15 | Old Section 6 | The rare failure mode section (with its table and figure) was removed | The mechanism is not settled, and the mentor asked for it to go |
| 16 | New Section 6 | The spread score S, the reference version D, the 60 runs in four states, the threshold chosen on validation and tested on test, a table and Figure 6 | Reviewer comments from the mentor. Numbers come from `reports/diagnostic_eval.json` |
| 17 | New Section 7 | NASA C-MAPSS turbofan data as a second dataset, with a table. Pooling shrinks the signal about nine times and the model keeps working | Reviewer comments from the mentor. Numbers come from `reports/second_dataset.json` |
| 18 | Section 8 | The two paragraphs on scope and on selection biases, and the economics figure, were removed. The table stays | Asked to reduce it |
| 19 | Limitations | Rewritten as six shorter bullets that match the new sections | Follows from 15 to 17 |
| 20 | Abstract, Conclusion | The abstract no longer mentions the second failure and now mentions the threshold and the turbofan data. One sentence was added to the Conclusion | Follows from 15 to 17 |
| 21 | Word file | The seven figures were missing from the earlier root copy of the Word file (the images were in the file but the pages did not point to them). They were put back, and the figures were renumbered to match | A fault in the earlier copy, found while updating it |
| 22 | Throughout | The co-author's revisions were merged: the title and tree claims narrowed to the tested XGBoost baseline, a related-work comparison table (four new references), a mission-assurance subsection, the label-free versus calibrated threshold wording, a Wilson interval for the 4/5 collapse rate, and a five-split T0 economics summary | Reviewer questions on scope and threshold. Our own threshold wording was changed to say the AUC cutoff was chosen after the results were seen |
| 23 | Introduction, Section III, Section IV | Informal wording rewritten in plain scientific language ("another kettle of fish", "This isn't, of course, comfortable", "isn't a straw man", "the fix is easy", "Someone could say") and the remaining contractions expanded | Reviewer notes on language |
| 24 | Introduction, Related Work, Section IV, abstract | The claim that a mixed validation score "remained high" was replaced by measured values. For Mercury, Venus and Mars pooled, the AUC falls from 0.9995 to 0.875 under grouped normalisation, against 0.687 for Venus alone | `reports/diagnostic_protocol.json`. The old claim came from the original incident and is not in the saved artifacts |
| 25 | Section VI | The protocol is stated step by step. The AUC cutoff of 0.85 was set after the validation and test AUCs were seen. A cutoff sweep, a threshold set on other seeds, four other label-free summaries, batch size and temperature checks were added, with a new table | Reviewer notes on threshold selection. All numbers from `reports/diagnostic_protocol.json`, made by `src/ml/diagnostic_protocol.py` |
| 26 | Limitations | The threshold bullet now says a single threshold can be set only for cutoffs of 0.85 and 0.90, and that single-outcome batches were not tested | Follows from 25 |

---

## Still open

- **Keywords.** EAAI prefers single word keywords. The original six were kept.
- **Table III spread.** It uses the population standard deviation over 5 seeds (divide by n). The authors decided to keep it.
- **Inspec codes and ORCIDs.** None supplied.
- **Statements written during the conversion.** The competing interest, CRediT roles and funding statements were not in the Word file. They need to be confirmed by the authors before submission.
- **BibTeX warnings.** Nine entries have no page numbers because none were given. None were invented.

---

## Double anonymised split

- `title_page.tex` and `title_page.pdf`: authors, affiliation, corresponding author, competing interest, CRediT and funding.
- `manuscript_anonymous.tex` and `manuscript_anonymous.pdf`: the review file, with authors and the repository URL removed.
- `manuscript.tex` and `manuscript.pdf`: the full version with author names, for the authors.
- `highlights.docx`: upload as a separate file.

---

## How the final text was checked

- 29 measured claims in the paper were compared with `reports/`, and all match. The numbers in Sections 6 and 7 were compared with `reports/diagnostic_eval.json` and `reports/second_dataset.json` after the text was written.
- Every table cell was compared with `reports/`, and all match.
- All 40 references are cited, and every DOI was resolved and its title compared with the entry.
- The compiled PDFs have no unresolved references, and the anonymous PDF contains no author names.

---

## How to rebuild

```powershell
.\compile.ps1
```

or

```
pdflatex manuscript.tex
bibtex manuscript
pdflatex manuscript.tex
pdflatex manuscript.tex
```

Main files: `manuscript.tex`, `references.bib`, `elsarticle-harv.bst`, `fig1.png` to `fig6.png`.
