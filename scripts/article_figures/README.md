# Canonical article-figure workflow

This directory reconstructs Figures 1-16 of *Lorenz Energy Cycle Climatology
for the Southwestern Atlantic Cyclones* as a literal published-versus-corrected
comparison.

## Scientific definition

| Side | Population | Lifecycle rows |
|---|---:|---:|
| Before - archived article | 6,789 cyclones | 25,000 |
| After - validated corrected rerun | 3,820 cyclones | 15,829 |

Primary-phase panels use exact `period == phase` rows. Total-lifecycle EOFs use
the mean of every archived period for each cyclone and the correlation matrix
of the 24 published LEC terms. Corrected EOFs are fitted independently, then
matched and sign-aligned to legacy loading patterns.

PC extremes are screened across PCs 1-8 and retained when their dominant mode
is EOF 1-4. Intense systems use the pointwise 90th-percentile vorticity
criterion and five K-means groups fitted to the first eight aligned
total-lifecycle PC scores. Figure 16 contains mean LECs of positive EOF cyclone
groups.

Because the populations differ, the canonical report combines correction and
population effects. The separate `scripts/lec_rerun_comparison/` workflow is
the correction-only paired control.

## Inputs

- full legacy cache: 6,789 cyclone IDs and 25,000 rows;
- corrected cache: 3,820 cyclone IDs and 15,829 rows;
- frozen South Atlantic track database with time, position and 850-hPa
  vorticity.

Input hashes and population assertions are written to provenance and checked
before figures are generated.

## Run

```bash
python scripts/article_figures/generate_article_comparison.py \
  --legacy-cache /path/to/energy_cache.parquet \
  --corrected-cache /path/to/energy_cache_corrected.parquet \
  --tracks /path/to/tracks_SAt_filtered_with_energetics_processed.csv \
  --output-root "$PWD"

python scripts/article_figures/build_article_comparison_report.py \
  --output-root "$PWD"
```

Use `--resume-after-13` only when the existing Figure 1-13 PNG/PDF pairs were
created from the same inputs; the command validates their presence before
continuing.

## Outputs

```text
figures/paper/                                  20 PNG + 20 vector PDF files
results/article_comparison/                     tables, assignments and hashes
docs/lec_climatology_article_before_after_report.md
docs/lec_climatology_article_before_after_report.pdf
```

The figure manifest records SHA-256 hashes for each PNG/PDF pair. Provenance
records both input hashes, population sizes, source/toolkit commits and EOF
variance landmarks.

## Figure layout

- Figure 3: archived distributions above, corrected distributions below.
- Figures 4-8 and 12: dark legacy arrows/values and red corrected values.
- Figures 9, 10, 11, 13 and 14: before above, after below.
- Figure 12: split into 12a (all intense) and 12b (five clusters).
- Figure 15: before left, after right.
- Figure 16: four files, each with before left and after right.

## Verification

```bash
pytest -q tests/test_article_figures.py
```

After generation, verify that the manifest contains 20 entries, that legacy
total EOF 1-4 variance is 28.304%, 11.018%, 10.925% and 8.188%, and visually
inspect a full Poppler rendering of the report.

`generate.py`, `generate_comparison.py` and `build_report.py` remain internal
historical/helper modules because the canonical generator imports several of
their plotting primitives. Do not use their command-line entry points for a
paper product.
