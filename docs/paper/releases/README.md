# Paper archive

Snapshots of the paper as it was at each point worth going back to. The live
paper is one directory up; **these are frozen copies, not the working files.**
Do not edit anything here — regenerate from `docs/paper/content.py` instead.

Naming: `OrbitGuard_v<n>_<format>_<date>.<ext>`.

| Version | Date | Format | What changed |
|---|---|---|---|
| v1 | 2026-08-23 | single-column Word | The first generated draft. Related Work was a stub, everything was single-seed, no figures, no bibliography. |
| v2 | 2026-09-10 | IEEE conference | Two-column IEEEtran, 7 figures, 32 references, five-seed replication, full Related Work. Final author list. |
| v3 | 2026-09-10 | IEEE journal | Same content, `journal` class — authors on one line, affiliation as a footnote. Adds the Code and Data Availability section. **This is the submission target.** |

## Which one do I send?

**v3.** v2 exists because the paper was drafted for a conference before the
venue changed, and a reviewer may ask to see it. v1 is kept only so the
difference between "a draft" and "a paper" is visible in one place.

## Rebuilding any of these

The current paper regenerates from source; the archived ones do not, because
the artifacts they were built from have since been overwritten by later runs.
That is the point of freezing them.

```bash
python docs/paper/render_latex.py                    # journal (default)
python docs/paper/render_latex.py --mode conference  # conference
python docs/paper/build_paper.py                     # Word
```

Then compile with `pdflatex` + `bibtex` (twice), or Overleaf. `IEEEtran.cls`
and `IEEEtran.bst` are vendored one directory up, so no TeX Live
publisher-styles install is needed.

## Adding a new version

Copy the built files in with the next version number and add a row above. Keep
the old ones — the whole reason this directory exists is that the numbers in
the paper changed as experiments were re-run, and it should be possible to see
which version of a claim someone was reading.
