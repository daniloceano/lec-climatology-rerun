# Article figure workflow

The article comparison uses 6,789 legacy cyclones (25,000 lifecycle rows) and 3,820 corrected cyclones (15,829 rows). Corrected phase and total-lifecycle EOFs are fitted independently, then matched and sign-aligned to the published reference. The published Figure 9–16 logic uses PC extremes among modes 1–8, a common track-level 90th-percentile maximum-vorticity threshold, and four clusters of intense systems. The corrected figures retain the published layout.

The input paths and pinned hashes are in `config/data_sources.toml`. Run from the repository root:

```bash
python scripts/sync_swell_inputs.py
python -m scripts.article_figures.reproduce_downstream
python -m scripts.article_figures.build_article_results
python -m scripts.article_figures.build_validated_comparison
python -m scripts.article_figures.generate_corrected_article_table
python -m pytest -q
```

`reproduce_downstream` first validates the archived legacy PCs, EOF-extreme memberships, intense selection, four clusters and Figures 12–14/16 definitions. The gate evidence is in `results/original/article/reproduction_gate/`. It then writes corrected Figure 9–16 PNG/PDF pairs, their numerical products and hashes directly to `figures/corrected/article/` and `results/corrected/article/`. `build_article_results` places the gate's validated legacy products under `results/original/article/` and combines them with the corrected products into versioned CSVs under `results/comparison/article/`. `build_validated_comparison` refreshes the eight paired figures and 16-figure manifest. Figures 1–8 and their phase EOF inputs are retained as validated products.

Table 1 retains the published LaTeX layout. Its corrected statistics pool all 15,829 lifecycle-period rows, with full precision and a hash manifest in `results/corrected/article/`. Presentation files are in `tables/corrected/article/`.

The original, corrected and comparison directories are the only article result and figure families. The fixed-population paired-control study is separate. Older plotting entry points with the superseded clustering or Figure 16 definitions are blocked. See [the reproduction report](../../docs/technical/downstream_reproduction.md) for validation details.

## Supplementary Figures S1–S4

The final-submission supplement has four figures. The original PNGs are copied
verbatim; corrected products use the validated EOF/cluster results and archived
tracking fields. Figure S4 requires per-timestep corrected `Ck` from the
production run. Extract it read-only on `swell`, then build all three result
families:

```bash
mkdir -p tmp/supplementary
ssh -o BatchMode=yes swell 'python - /p1-swell/danilocs/lec_climatology_corrected_v2' \
  < scripts/article_figures/extract_corrected_decay_ck.py \
  > tmp/supplementary/ck_corrected.csv
ssh -o BatchMode=yes swell \
  'sha256sum /p1-swell/danilocs/lec_climatology_corrected_v2/population_manifest.csv /p1-swell/danilocs/lec_climatology_corrected_v2/provenance.json' \
  > tmp/supplementary/remote_sha256.txt
python -m scripts.article_figures.build_supplementary
```

The extractor reads the production files without changing them. The build
requires the local archived manuscript scripts and track tables at the paths
used by the main reproduction. Its S1 legacy count gate checks the published
bar labels. See [the supplementary report](../../docs/comparison/supplementary_report.md)
for the q95/q99 and vorticity-caption discrepancies.
