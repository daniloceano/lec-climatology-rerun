# Figures

## `original/article/`

The 16 PNGs referenced by the final revision-2 article submission. They are
copied verbatim from the legacy manuscript directory and are never overwritten
by corrected outputs.

## `corrected/article/`

Corrected-only reusable artifacts. Figures 1 and 2 are present because they do
not depend on corrected LEC values. Corrected content for Figures 3–16 remains
in the canonical comparison panels, avoiding a redundant second visual suite.

## `comparison/article/`

The 20 PNG/PDF pairs used by
`docs/comparison/article_before_after_report.pdf`:

- Figures 1-11;
- Figure 12a (all intense systems) and 12b (five PC groups);
- Figures 13-15;
- Figures 16a-16d (one before/after panel per EOF group).

These figures compare the full archived article population with the validated
corrected rerun. Generate them with
`scripts/article_figures/generate_article_comparison.py`.

## `comparison/paired_control/`

Technical diagnostics on the same 3,820 cyclones before and after correction.
They support the paired-control report and are not paper figures.

The obsolete four-cluster corrected set remains only in Git history because it
does not match the current five-group article-comparison definition.
