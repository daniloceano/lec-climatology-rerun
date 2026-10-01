# Article tables

`original/article/table_01_lec_summary_statistics.tex` is extracted verbatim
from the final revised manuscript. `corrected/article/` preserves that table's
caption, columns, row order, labels, two-decimal formatting and LaTeX layout,
while replacing the numeric cells with statistics from the validated corrected
cache.

The corrected directory contains:

- the table block for inclusion in a manuscript;
- a standalone compilable LaTeX document;
- a Markdown rendering for quick review.

Regenerate all forms from the pinned ignored swell input with:

```bash
python scripts/sync_swell_inputs.py
python scripts/article_figures/generate_corrected_article_table.py
```

Full-precision values and SHA-256 provenance are stored under
`results/corrected/article/`. The published calculation pools all
lifecycle-period mean rows (15,829 in the corrected cache); it does not first
collapse each cyclone to a single value.
