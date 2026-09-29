# Results

## `original/article/` and `corrected/article/`

Lossless `version=before` and `version=after` row views of the canonical
comparison CSVs. They are produced by
`scripts/article_figures/materialize_version_views.py`; each directory has a
provenance file with source/output hashes and row counts. No scientific values
are recalculated.

`corrected/article/reproduction/` is separate: it contains the freshly
recalculated tables, assignments, four-cluster products, figure manifest and
provenance for the 16 corrected figures that retain the publication layout.

## `comparison/article/`

Canonical numerical products behind `figures/comparison/article/`:

- phase statistics;
- phase and total-lifecycle EOF loadings and variance;
- total-lifecycle PC scores and extreme assignments;
- five-group intense-cyclone assignments, centroids and statistics;
- `figure_manifest.csv` with PNG/PDF hashes;
- `provenance.json` with input hashes, population counts and audited commits.

The small CSV/JSON files are versioned. Rebuild them with
`scripts/article_figures/generate_article_comparison.py`.

## `comparison/paired_control/`

Correction-only summary tables for the fixed 3,820-cyclone population. Large
reproducible parquet intermediates remain ignored by Git.
