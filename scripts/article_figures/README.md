# Article artifact workflow

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

PC extremes are screened across PCs 1–8 and retained when their dominant mode
is EOF 1–4. The validated downstream workflow uses a common track-level
90th-percentile maximum-vorticity threshold and four K-means groups fitted to
the first eight aligned total-lifecycle PC scores. Figure 16 contains the
article's phase/EOF-loading synthesis.

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

## Corrected figures in the original article layout

The standalone corrected suite preserves the publication's 16-file layout and
four-cluster intense-system analysis. It reuses the frozen manuscript drawing
functions while supplying the corrected cache and authoritative track table.
Figures 1–2 remain unchanged; Figures 3–16 are recalculated.

Figures 5–8 use **published/reference identity**, shared with the article
comparison. Figure 16 uses their frozen matched phase EOF inputs.

```bash
python scripts/sync_swell_inputs.py
python -m scripts.article_figures.reproduce_downstream
python -m scripts.article_figures.build_validated_comparison
```

Inputs and access locations come from `config/data_sources.toml`. Current
Figures 9–16 are written to `figures/corrected/article/`, with scientific
products in `results/corrected/article/validated_downstream/`. Earlier
Figures 1–8 retain their existing products.

### Regenerate only Figures 5–8

```bash
python scripts/article_figures/regenerate_phase_eofs.py
python -m pytest tests/test_article_figures.py tests/test_phase_eof_matching.py -q
```

This verifies the legacy/corrected caches against the existing article provenance,
uses the frozen manuscript renderer without editing it, and regenerates only
Figures 5–8 in both layouts. Figures 1–4 and 9–16, total EOFs/PCs, extreme
assignments, clustering, original results and inputs are preserved and hash-checked.

The methodological gate was verified: each primary phase has its own matrix of
observations × 24 terms and its own `compute_eof`/`np.linalg.eigh` call. Legacy
phase sample sizes are 4,587 / 6,642 / 4,747 / 6,488; corrected samples are 3,820
per phase. Therefore the existing eight-mode `align_eofs` assignment is applied
**separately within each phase**, never across phases or to total-lifecycle PCs.

Canonical files are in `results/comparison/article/phase_eof_matched/`:

- `loadings.csv` and `variance.csv`: both renderers consume this same product.
- `reference_eof`: identity of the archived published/reference pattern.
- `raw_rank`: descending eigenvalue rank within the decomposition of that
  version and phase, before matching. On an `after` row it is the corrected rank.
- `sign_alignment`: +1 or −1 applied jointly to raw loadings and PC columns.
- The variance travels with its matched raw mode; a sign flip does not affect EV.
- `consistency.csv`: differences for all 16 panels; both numerical differences
  must be zero. `provenance.json` hashes inputs, code and direct outputs;
  `frozen_outputs.json` pins the unrelated products preserved by the update.

The existing comparison and materialized view CSVs retain `eof` **only as a
compatibility alias for reference identity** and `matched_rank` for raw rank;
their numerical contents are unchanged. The corrected reproduction CSVs now use
the explicit schema above. Its phase score columns are `reference_PC1` through
`reference_PC8`. The `_raw.csv` phase tables retain raw-rank values for audit;
Figures 5–8 and the validated Figure 16 use the matched phase product.

For incipient, reference EOF 2 → raw 3 → **10.548160122%**, and reference EOF 3
→ raw 2 → **14.023895264%**. These are regression expectations, not hard-coded
permutations. See `docs/comparison/phase_eof_matching_correction.md` for the full
mapping, validation and Figure 16 methodological boundary. Existing assembled
report PDFs were not rebuilt; use the regenerated individual figures.

## Corrected table in the original article layout

Table 1 pools the lifecycle-period means exactly as the archived generator did:
25,000 rows in the publication and 15,829 rows in the corrected rerun. It does
not first compute one total-lifecycle mean per cyclone. Energy reservoirs are
divided by $10^5$; standard deviation uses `ddof=1`; all displayed values use
two decimals.

```bash
python scripts/sync_swell_inputs.py
python scripts/article_figures/generate_corrected_article_table.py
```

The command extracts the final-submission table verbatim, retains its caption,
column order, term labels and LaTeX structure, and replaces only the 24 rows of
statistics. Outputs are under `tables/original/article/`,
`tables/corrected/article/` and `results/corrected/article/reproduction/`.
The standalone `.tex` file is provided for independent compilation and visual
inspection.

## Historical comparison generator (superseded for Figures 9–16)

The commands below document the old 20-panel workflow. Use the validated
downstream commands at the end of this file for current Figures 9–16.

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

## Historical outputs

```text
figures/comparison/article/                    historical 20-panel layout
results/comparison/article/                     tables, assignments and hashes
docs/comparison/article_before_after_report.md
docs/comparison/article_before_after_report.pdf  (historical)
```

The comparison CSVs can be separated without numerical recomputation with
`materialize_version_views.py`, which writes hash-traceable `before` and
`after` views under `results/original/article/` and
`results/corrected/article/`.

The figure manifest records SHA-256 hashes for each PNG/PDF pair. Provenance
records both input hashes, population sizes, source/toolkit commits and EOF
variance landmarks.

## Historical figure layout (superseded for Figures 9–16)

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

## Validated downstream figures (2026-09-30)

Use `python -m scripts.article_figures.reproduce_downstream` for Figures 9–16.
It first validates the legacy PC scale, archived memberships, four clusters,
Figure 12 annotations, original density grids and original statistics. Any gate
failure prevents corrected generation. `--legacy-only` runs just that gate.
Current PNG/PDF files are in `figures/corrected/article/`;
new numerical products and provenance are in
`results/corrected/article/validated_downstream/`. Canonical Figures 5–8 stay frozen; the prior Figures 9–16 are replaced. Build the before/after panels with `python -m scripts.article_figures.build_validated_comparison`.
The older generators remain blocked because
they still implement superseded downstream definitions. See
[the reproduction report](../../docs/technical/downstream_reproduction.md).
