# Figures 5–8: phase EOF identity correction

Historical scope note (2026-09-30): the Figure 16 statements below describe
the state before the validated downstream reproduction. Current Figure 16 uses
the frozen matched phase EOF inputs from Figures 5–8; see
[`downstream_reproduction.md`](../technical/downstream_reproduction.md).

## Methodological gate: confirmed

This supersedes the stopped status of `eof_matching_audit_2026-09-29.md`.
The user accepted the audited mapping and corrected the requested EV regression
before authorizing implementation. The initial diagnostic directory remains a
historical record of the pre-fix inconsistency, not the current figure inputs.

`primary_phase_rows` selects exact `period == phase` rows. The old standalone
path used equivalent filtering in `load_inputs`. `independent_eof_by_phase`
then selects a separate matrix for each phase and each version, sorts track IDs,
and calls `compute_eof` inside the phase loop. `compute_eof` standardizes that
matrix, constructs its own 24×24 correlation matrix and invokes `np.linalg.eigh`.
Instrumented execution and the permanent integration test confirm **eight separate
calls**, each containing one phase only. There is no global PCA split after fitting.

| Phase | Legacy matrix | Corrected matrix |
|---|---:|---:|
| incipient | 4,587 × 24 | 3,820 × 24 |
| intensification | 6,642 × 24 | 3,820 × 24 |
| mature | 4,747 × 24 | 3,820 × 24 |
| decay | 6,488 × 24 | 3,820 × 24 |

All selected observations were complete: no rows were removed by `compute_eof`.
Legacy is the complete archived population (6,789 cyclones); corrected is the
validated rerun population (3,820 cyclones). Input SHA-256 checks passed before
recalculation. No cache or manuscript file was modified.

## Root cause and implementation

The comparison already matched within each phase through `align_eofs`.
The standalone corrected reproduction called `eof_by_phase` and used raw rank
as its displayed EOF label. Its raw EOF 2/incipient was therefore presented
under the same label as the comparison's reference EOF 2 (corrected raw 3).
The materialized original/corrected views had not lost the matching.

`phase_eofs.matched_phase_eofs` reuses `independent_eof_by_phase` and its existing
`align_eofs` assignment; no second matching algorithm was introduced.
`independent_eof_by_phase(return_details=True)` now exposes corrected PCs and
raw-rank/sign metadata alongside the already aligned loadings and EV. Numerical
EOF computation and the total-lifecycle methods are unchanged.

Both generators write/read the same canonical phase loading/variance product at
`results/comparison/article/phase_eof_matched/`. The corrected-only generator
selects its `after` rows. A dedicated regeneration entry point invokes only the
Figure 5–8 renderers and updates their manifests/provenance. Existing comparison
CSV numbers and original/materialized views are preserved byte-for-byte.

Definitions:

- **Raw rank:** descending eigenvalue order in the phase/version decomposition.
- **Reference EOF:** the published/reference pattern identity being compared.
- **Matched mode:** the raw corrected mode assigned one-to-one to that reference
  by maximum total absolute Pearson pattern correlation across all eight modes
  and all 24 terms, within the same phase.
- **Sign alignment:** arbitrary global orientation chosen to agree with the
  reference. It multiplies the loading and its PC together, never EV.

New phase tables use `reference_eof`, `raw_rank`, and `sign_alignment`.
Old comparison/view tables retain `eof` solely as a reference alias and
`matched_rank` as the corrected raw rank. Corrected phase scores now use
`reference_PC1`…`reference_PC8`, jointly reordered and sign-aligned. Explicit
`*_by_phase_raw.csv` snapshots retain the raw convention for Figure 16.

The comparison panels display `after: raw n` where rank swaps occur. The
corrected-only publication layout is retained; its manifest links each Figure
5–8 to the canonical table containing raw rank, sign, correlation and EV.

## Final mapping

EV is percent; sign is relative to the existing largest-loading-positive raw
orientation. Matching does not establish perfect physical equivalence.

| Phase | Reference EOF | Corrected raw rank | Sign | Correlation | EV published | EV corrected |
|---|---:|---:|---:|---:|---:|---:|
| incipient | 1 | 1 | +1 | 0.855490 | 20.788841 | 20.579724 |
| incipient | 2 | 3 | -1 | 0.773920 | 13.704764 | 10.548160 |
| incipient | 3 | 2 | +1 | 0.939059 | 11.978393 | 14.023895 |
| incipient | 4 | 4 | +1 | 0.820713 | 8.662667 | 8.864907 |
| intensification | 1 | 1 | +1 | 0.823593 | 28.626835 | 27.549174 |
| intensification | 2 | 2 | +1 | 0.712858 | 12.327574 | 14.148976 |
| intensification | 3 | 4 | +1 | 0.628135 | 11.039103 | 9.471775 |
| intensification | 4 | 3 | +1 | 0.913373 | 8.831482 | 10.547213 |
| mature | 1 | 1 | +1 | 0.771619 | 28.471949 | 26.303650 |
| mature | 2 | 2 | +1 | 0.691257 | 11.727633 | 11.802134 |
| mature | 3 | 3 | +1 | 0.519532 | 9.953698 | 10.205477 |
| mature | 4 | 4 | +1 | 0.810214 | 8.543631 | 9.303124 |
| decay | 1 | 1 | +1 | 0.798747 | 29.026954 | 29.174583 |
| decay | 2 | 2 | +1 | 0.799739 | 10.601571 | 11.071529 |
| decay | 3 | 3 | +1 | 0.719308 | 9.725767 | 9.079099 |
| decay | 4 | 4 | +1 | 0.686246 | 8.415873 | 8.041286 |

## Validation and reproducibility

Commands:

```bash
python scripts/article_figures/regenerate_phase_eofs.py
python -m pytest tests/test_article_figures.py tests/test_phase_eof_matching.py -q
git diff --check
```

- The original comparison values reproduce within CSV precision (8 significant
  digits): loading tolerance 5e-8, EV tolerance 5e-7 percentage points. Serialized
  canonical/compatibility/corrected-only values and the actual renderer inputs
  agree **exactly** for all 16 panels. `consistency.csv` records zero differences.
- Eight new test cases (four parameterized phases plus four integration/schema/
  renderer/provenance tests) complement the ten existing article tests:
  **18 passed, zero failures/skips/warnings on this host**.
- Tests independently match stored raw patterns; enforce one-to-one assignments;
  check 32 individual sign inversions; verify joint loading/PC/EV permutation;
  assert all audited ranks and the two incipient variances; reject ambiguous raw
  schema and mismatched metadata; intercept all 16 actual renderer panels; and
  verify protected downstream/output hashes. The real-input integration test
  explicitly skips only when the external pinned caches are absent on another host.
- Numerical sign checks use absolute tolerance 1e-12. Serialized PC checks allow
  relative 5e-8 plus absolute 5e-9 for the eight-significant-digit CSV roundoff.
- Initial development test failure: integer serialized track IDs were compared
  to string IDs from the cache. The canonical preparation now normalizes IDs to
  int64 as the existing input loaders do; the score check selects only PC columns.
  No EOF matching expectation was relaxed.
- PNGs retain the published standalone dimensions. All eight PDFs are single-page
  documents and were rendered with Poppler for visual inspection. The raw-rank
  panel label was shortened to avoid extending into the conversion arrows.
- `frozen_outputs.json` verifies **155 unrelated output files** byte-for-byte.
  The input hashes, code hashes and hashes of all direct outputs are recorded
  in canonical `provenance.json`; existing figure manifests were updated.

## Frozen downstream products and scientific boundary

**Figure 16 was not regenerated.** The corrected reproduction still represents
raw phase loadings passed to `render_syntheses`/`plot_period_means(..., 'min_max')`.
Its raw input is explicitly preserved in `eof_loadings_by_phase_raw.csv`.
The full generator retains a separate `raw_phase_loadings` variable for this
path; it never receives the matched Figure 5–8 input. The comparison Figure 16
instead depicts mean LECs for positive total-PC extreme groups. Before changing
Figure 16, decide whether the standalone synthesis should retain raw rank or
follow reference identity, and reconcile its distinct scientific definition.
It must not be assumed consistent with the new phase reference labels.

Figures 9–10 and 11 derive assignments from separately fitted total-lifecycle PCs.
The full generators retain their original `total_eof`/`independent_total_eof`,
`assign_published_eof_extremes`, and clustering calls. The targeted command never
calls those functions. Total-lifecycle loadings, variance, PCs, extreme assignments,
intense-cyclone clustering and all Figure 16 files are unchanged. The paired
control is also unchanged; its population/period convention remains separate.

Figures 1–4 and 9–16, original figures/results, tables and historical diagnostics
were preserved. Existing assembled report PDFs were not regenerated, so their
embedded old figure images are historical; use the new individual PNG/PDF files.

## Remaining uncertainty

The Figures 5–8 products now share an unambiguous reference identity and can be
used as that corrected figure set. A lower correlation (e.g. mature reference
EOF 3: 0.519532) still warrants scientific interpretation. Differences include
population changes as well as the toolkit correction. Figure 16's definition and
cross-workflow total-PC conventions remain separate review items, not repaired
or implicitly approved by this phase-only change. No push or additional commit
was made for this correction; the work remains reviewable in the current branch.

## Output inventory

Only the following figure pairs were regenerated:

| Figure | Corrected-only PNG / PDF | Comparison PNG / PDF |
|---|---|---|
| 5 | [PNG](../../figures/corrected/article/fig_05_eof1_lec.png) / [PDF](../../figures/corrected/article/fig_05_eof1_lec.pdf) | [PNG](../../figures/comparison/article/fig_05_eof1_lec_published_corrected.png) / [PDF](../../figures/comparison/article/fig_05_eof1_lec_published_corrected.pdf) |
| 6 | [PNG](../../figures/corrected/article/fig_06_eof2_lec.png) / [PDF](../../figures/corrected/article/fig_06_eof2_lec.pdf) | [PNG](../../figures/comparison/article/fig_06_eof2_lec_published_corrected.png) / [PDF](../../figures/comparison/article/fig_06_eof2_lec_published_corrected.pdf) |
| 7 | [PNG](../../figures/corrected/article/fig_07_eof3_lec.png) / [PDF](../../figures/corrected/article/fig_07_eof3_lec.pdf) | [PNG](../../figures/comparison/article/fig_07_eof3_lec_published_corrected.png) / [PDF](../../figures/comparison/article/fig_07_eof3_lec_published_corrected.pdf) |
| 8 | [PNG](../../figures/corrected/article/fig_08_eof4_lec.png) / [PDF](../../figures/corrected/article/fig_08_eof4_lec.pdf) | [PNG](../../figures/comparison/article/fig_08_eof4_lec_published_corrected.png) / [PDF](../../figures/comparison/article/fig_08_eof4_lec_published_corrected.pdf) |

The explicit raw loading/variance snapshots were also compared numerically to
the pre-correction `HEAD` tables: both agree exactly after sorting by phase,
raw rank and term. This preserves the meaning of the frozen Figure 16 input.

Modified implementation: `common.py` (expose jointly aligned PCs/metadata),
`phase_eofs.py` (canonical explicit product and pinned inputs),
`generate_article_comparison.py` and `generate_corrected_article.py` (shared
source; raw Figure 16 path separate), `generate_comparison.py` (reference
selection and compact raw-rank label), and `regenerate_phase_eofs.py` (targeted
regeneration and preservation checks). Permanent tests are in
`tests/test_phase_eof_matching.py`; workflow documentation is in
`scripts/article_figures/README.md` and this report.
