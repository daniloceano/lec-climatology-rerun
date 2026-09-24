# Results

## `article_comparison/`

Canonical numerical products behind `figures/paper/`:

- phase statistics;
- phase and total-lifecycle EOF loadings and variance;
- total-lifecycle PC scores and extreme assignments;
- five-group intense-cyclone assignments, centroids and statistics;
- `figure_manifest.csv` with PNG/PDF hashes;
- `provenance.json` with input hashes, population counts and audited commits.

The small CSV/JSON files are versioned. Rebuild them with
`scripts/article_figures/generate_article_comparison.py`.

## `paired_control/`

Correction-only summary tables for the fixed 3,820-cyclone population. Large
reproducible parquet intermediates remain ignored by Git.

The obsolete `lec_climatology_corrected/` results were removed together with
the misleading earlier figure set. Git history preserves them if an audit
needs the exact former state.
