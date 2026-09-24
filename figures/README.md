# Figures

## `paper/`

The only manuscript-facing figure set. It contains the 20 PNG/PDF pairs used
by `docs/lec_climatology_article_before_after_report.pdf`:

- Figures 1-11;
- Figure 12a (all intense systems) and 12b (five PC groups);
- Figures 13-15;
- Figures 16a-16d (one before/after panel per EOF group).

These figures compare the full archived article population with the validated
corrected rerun. Generate them with
`scripts/article_figures/generate_article_comparison.py`.

## `paired_control/`

Technical diagnostics on the same 3,820 cyclones before and after correction.
They support the paired-control report and are not paper figures.

The obsolete `lec_climatology_corrected/` set was removed because it mixed a
paired population with article-style figure numbering and could be mistaken
for the literal article comparison. It remains recoverable from Git history.
