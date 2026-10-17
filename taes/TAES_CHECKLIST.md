# TAES check

Source of the rules: the AESS "Information for Authors" page for IEEE Transactions on
Aerospace and Electronic Systems, https://ieee-aess.org/publications/transactions-aes/author-information,
and the official TAES LaTeX template (`TAES Template.zip` linked from that page).
The page says nothing about biographies, reference style, figure resolution or the
abstract length, so those lines say so.

## What the paper meets

| Rule | Status |
|---|---|
| Two column, single spaced, 10 point, PDF | Met. Built with the official `IEEEtaes` class (`taes/manuscript_taes.tex`) |
| Regular paper, not a survey | Met |
| Reference list in the TAES style | Met. Uses `IEEEtaes.bst`, numbered, 44 entries |
| Abstract is one paragraph, no equations, no numbered citations, no footnotes | Met. 220 words |
| Index terms in alphabetical order | Met. Six terms |
| Avoid "new" and "novel" in the title and abstract | Met. Neither word appears |
| Search keywords in the title and abstract | Met |
| Single anonymous review, so the authors are named | Met. The anonymous file is not needed |
| Supplementary material with a readme | Met. Code, result files and readme are in the public repository, linked on the first page |
| Biographies | Added after the references. See "Still needed" |

## What needs a decision or an action

1. **Do not submit the same paper to EAAI and TAES at the same time.** TAES says
   submissions must be original, must not be under review elsewhere, and that
   multiple submissions are prohibited. A paper that was rejected elsewhere has to
   be disclosed at submission. Decide which journal gets it.
2. **Length.** There is no page limit, but an accepted regular paper pays $200 for
   each printed page beyond 10, and very long papers may get worse reviews. In the
   TAES template this paper is 12 pages, which is about $400 if IEEE's proof also
   comes to 12. Photos in the biographies could add part of a page. Authors from
   countries under US financial sanctions have a hard limit of 10 pages.
3. **AI disclosure.** TAES rejects papers with undisclosed AI use. The
   Acknowledgment now names Claude, says what it did (code, first drafts of the
   text, checking references and numbers) and how large the involvement was.
   **Please confirm the wording is true for you.** It says the first drafts of all
   sections were written with the tool.
4. **Biographies.** The three biographies are placeholders with only the facts the
   repository gives (name and school). Send the degree and year, research interests
   and anything published for each author, and the position and degree of the guide.
   TAES asks for photos for the final version, not for review.
5. **Funding, grant numbers and ORCIDs.** The first page says there was no specific
   grant. Change it if that is not right.
6. **Emails.** Only the corresponding author's email is on the first page.

## Advice, not rules

- The text uses British spelling (normalisation, behaviour, labelled) and about 30
  contractions (isn't, it's). The TAES template itself uses American spelling
  ("acknowledgment"). IEEE copy editors usually change these. Not changed here,
  because it touches the text.
- Figures 3, 4 and 5 come out at about 270 dpi at column width. IEEE asks for sharper
  images in the final files. Figures 1, 2 and 6 are fine.
- Index terms are best taken from the IEEE Thesaurus. Ours are free terms.
- "Sections" are numbered with Roman numerals in the TAES version, as IEEE does.
  Table and figure numbers follow the order they appear in.

## Files

- `manuscript_taes.tex` and `manuscript_taes.pdf`: the TAES version, 13 pages.
- `make_taes.py`: rebuilds the `.tex` from `eaai/manuscript.tex`, so the text stays the same.
- `IEEEtaes.cls`, `IEEEtaes.bst`: the official class and bibliography style.
- `make_taes_word.py` and `OrbitGuard_TAES.docx` (repository root): the Word version, built from
  the official TAES Word template (`docs/paper/TAES_Word_Template.zip`, the Regular paper file).
  It uses the template's own page size, two columns, footers and paragraph styles, and takes its
  text from `manuscript_taes.tex`, so the Word and PDF versions say the same thing.
- The title is the one recommended in the review notes: "Detecting Prediction Collapse Caused by
  Pooled Feature Normalization in Space-Trajectory Screening". The spelling is American in the TAES
  versions only. The replication scripts listing is not in the TAES versions.
