# Phase EOF matching audit — 2026-09-29

## Status: stopped at the diagnostic gate

The requested expectation is contradicted by the pinned inputs. No production code,
existing results, figures, manifests, legacy data or server run was changed.
Only this report and a separate diagnostic directory were added.

**Incipient published EOF 2 maps to corrected raw mode 3, whose explained variance
is 10.548160122%, not 14.0239%.** Corrected raw mode 2 explains 14.023895264% and
maps to published EOF 3. Raw ranks are sorted by descending eigenvalue.
The signed correlations of published EOF 2 against corrected raw modes 2 and 3
are -0.217856423 and -0.773920005, respectively. After alignment, the matched
correlation is +0.773920005. Forcing 14.0239% onto matched raw mode 3 would attach
the variance of a different mode to its loadings.

The user explicitly required stopping if these data contradicted the proposed
expectation. Implementation, new regression tests and figure regeneration are
therefore pending review of that expectation. In particular, requested test B
cannot assert both raw mode 3 and variance 14.0239% for these inputs.

## Provenance and method

Reference repository commit: dcfd10c (before this diagnostic-only commit).
The reference is the full archived legacy population used by the existing article
comparison, not the paired-control sample. No alternate dataset was substituted.

- Legacy: 6,789 cyclones / 25,000 archived rows; 22,464 primary-phase rows.
- Corrected: 3,820 cyclones / 15,829 archived rows; 15,280 primary-phase rows.
- Primary phases require `period == phase`. Legacy phase counts are 4,587,
  6,642, 4,747, 6,488; corrected phase counts are 3,820 each.
- Exact input paths and verified SHA-256 hashes are in `verification.json`.
  Both recorded local copies of the corrected cache have the same pinned hash.
- Reused `primary_phase_rows`, `compute_eof`, and `align_eofs` from
  `scripts/article_figures/common.py`. Computed eight correlation-matrix EOFs
  per phase, with the existing 24-term order and track IDs sorted as in
  `independent_eof_by_phase`. Matched all eight modes one-to-one by maximizing
  the total absolute Pearson pattern correlation (Hungarian assignment).
- `published_eof` denotes the reference identity; `published_raw_rank` its
  legacy rank; `corrected_raw_rank` the rank before corrected permutation.
  `sign_alignment` multiplies the corrected loading and PC by +1 or -1.
  Sign diagnostics are relative to `compute_eof`'s largest-loading-positive
  convention; another raw sign convention would change this flag, not the
  aligned pattern. EV and maximum loading difference are computed after matching.
- Units of EV are percent (differences are percentage points). Pattern correlation
  uses all 24 loadings, including terms omitted from the four-box diagram.

## Diagnostic table (EOF 1–4)

| phase | published_eof | published_raw_rank | corrected_raw_rank | pattern_correlation | sign_alignment | sign_flip_applied | published_explained_variance_pct | corrected_matched_explained_variance_pct | rank_swapped | max_abs_loading_difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| incipient | 1 | 1 | 1 | 0.855490429 | 1 | False | 20.788840530 | 20.579724397 | False | 0.951010064 |
| incipient | 2 | 2 | 3 | 0.773920005 | -1 | True | 13.704763852 | 10.548160122 | True | 0.703418645 |
| incipient | 3 | 3 | 2 | 0.939058616 | 1 | False | 11.978392562 | 14.023895264 | True | 0.247321171 |
| incipient | 4 | 4 | 4 | 0.820713252 | 1 | False | 8.662666853 | 8.864907189 | False | 0.397447324 |
| intensification | 1 | 1 | 1 | 0.823592697 | 1 | False | 28.626834542 | 27.549173783 | False | 1.243626179 |
| intensification | 2 | 2 | 2 | 0.712857533 | 1 | False | 12.327573768 | 14.148976420 | False | 0.662157215 |
| intensification | 3 | 3 | 4 | 0.628134964 | 1 | False | 11.039102590 | 9.471774858 | True | 0.576862524 |
| intensification | 4 | 4 | 3 | 0.913373276 | 1 | False | 8.831481666 | 10.547212757 | True | 0.400674453 |
| mature | 1 | 1 | 1 | 0.771618724 | 1 | False | 28.471948683 | 26.303650261 | False | 1.426065312 |
| mature | 2 | 2 | 2 | 0.691256749 | 1 | False | 11.727633405 | 11.802134401 | False | 0.558823553 |
| mature | 3 | 3 | 3 | 0.519531944 | 1 | False | 9.953697915 | 10.205476981 | False | 0.636025028 |
| mature | 4 | 4 | 4 | 0.810214199 | 1 | False | 8.543630713 | 9.303124442 | False | 0.368144842 |
| decay | 1 | 1 | 1 | 0.798746917 | 1 | False | 29.026954318 | 29.174583327 | False | 1.383712365 |
| decay | 2 | 2 | 2 | 0.799739019 | 1 | False | 10.601570676 | 11.071528881 | False | 0.441675933 |
| decay | 3 | 3 | 3 | 0.719307591 | 1 | False | 9.725766988 | 9.079098820 | False | 0.512341696 |
| decay | 4 | 4 | 4 | 0.686245843 | 1 | False | 8.415872840 | 8.041286129 | False | 0.448291609 |

All eight modes are recorded separately in `diagnostic_all8.csv`. Additional
swaps outside the requested four modes are incipient 7↔8; intensification 5↔6
and 7↔8; decay 5→6, 6→7, 7→5. There are no mature swaps among the eight modes.

## Exact location of the divergence

`generate_article_comparison.py` calls `independent_eof_by_phase`, which applies
`align_eofs` to loadings, scores and variance together. In its output, `eof` is
the reference identity and `matched_rank` is the corrected raw rank.
`generate_comparison.py::fig_eof` selects both the loadings and variance by that
reference `eof`. Its current title does not expose the matched raw rank.
No lost permutation or double permutation was found in this path.

`materialize_version_views.py` only selects `before`/`after` rows. Both original
and corrected views preserve the comparison values exactly.

In contrast, `generate_corrected_article.py::main` calls `eof_by_phase(primary)`
without a reference or matching step. Its `eof` is the raw rank. These raw tables
are written under `results/corrected/article/reproduction/` and supplied to
`render_phase_and_eof_diagrams`. Its zero-based variance column conversion is
consistent with the frozen renderer and is not the cause of the discrepancy.

Thus the inconsistency is a mode-identity convention at preparation/materialization
of the standalone reproduction, then propagated to plotting. Each product plots
its own table consistently, but the same EOF label has different meanings across
the products. There is no evidence of an EOF eigenvalue calculation error.

The quoted corrected-only loadings (Ca≈-0.17, BAe≈-0.37, Gz≈+0.56, etc.) are
raw mode **2**, not 3. The quoted comparison loadings (Ca≈-0.08, BAe≈+0.64,
Gz≈-0.07, etc.) are sign-aligned raw mode **3**, not 2.

## Incipient / published EOF 2 loadings

| term | published_eof2 | matched_corrected_raw3 | unmatched_corrected_raw2 |
| --- | --- | --- | --- |
| Az | -0.134598363 | 0.066009331 | -0.203147923 |
| Ae | 0.559251370 | 0.402309036 | -0.537143377 |
| Kz | 0.258832998 | 0.338475004 | -0.303341826 |
| Ke | 0.120614138 | 0.073113841 | -0.298500563 |
| Cz | -0.446902629 | -0.280047395 | 0.385094677 |
| Ca | -0.121588457 | -0.078223560 | -0.171961734 |
| Ck | 0.295751890 | 0.052302476 | -0.146294151 |
| Ce | 0.301598348 | 0.115596195 | -0.230199938 |
| BAz | -0.445177754 | -0.399344891 | -0.084939259 |
| BAe | 0.790222143 | 0.638869964 | -0.371647718 |
| BKz | 0.026316856 | -0.224231654 | -0.500397760 |
| BKe | -0.065834026 | -0.174728856 | -0.314830956 |
| BΦZ | 0.733239779 | 0.364531197 | 0.476599665 |
| BΦE | 0.770362178 | 0.066943533 | 0.236907371 |
| Gz | -0.105115076 | -0.069266650 | 0.561200251 |
| Ge | -0.224650587 | -0.297270399 | 0.442376724 |
| ∂Az/∂t (finite diff.) | 0.070974762 | 0.388809065 | 0.425135213 |
| ∂Ae/∂t (finite diff.) | -0.279021325 | -0.327620287 | 0.193643529 |
| ∂Kz/∂t (finite diff.) | 0.147973564 | 0.409811889 | 0.408340331 |
| ∂Ke/∂t (finite diff.) | -0.071464374 | -0.093062930 | -0.227218157 |
| RGz | 0.151850403 | 0.451865384 | 0.584052477 |
| RKz | 0.052326506 | 0.379113812 | 0.546049711 |
| RGe | -0.569603711 | -0.688315108 | 0.415255942 |
| RKe | 0.058057127 | 0.094971980 | 0.255851605 |

## Numerical consistency checks

`product_consistency.csv` compares all 24 loading values and the EV supplied to
the two rendering paths at identical displayed EOF labels. Twelve of 16 panels
agree exactly in the stored CSVs. Four disagree: incipient EOFs 2 and 3, and
intensification EOFs 3 and 4. These are real pattern/rank differences, not merely
a global sign reversal. The largest stored loading discrepancies are 1.10357105,
1.03591786, 1.13537485 and 1.13537485, respectively.

Fresh phase recomputation agrees with all eight stored modes per phase within CSV
rounding: comparison loading error ≤4.9986e-9, EV error ≤4.6998e-7 percentage points;
raw reproduction loading error ≤4.9767e-9, EV error ≤4.2008e-7 percentage points.
Original/corrected materialized phase tables each equal the corresponding comparison
rows exactly (four table checks). All four assignments are one-to-one across eight
modes. Individually inverting each of eight raw modes in each of four phases
preserves matched loadings, aligned PCs, variance, ranks and correlations within
1e-12 (32 checks).

58 existing manifest/provenance hash checks passed: 16 Figure 5–8 PNG/PDF hashes,
40 source/output view table hashes and two view source-provenance hashes. Matching
hashes establish file integrity, not cross-product scientific consistency.
`verification.json` records these checks and the four diagnostic CSV hashes.

An initial ad hoc comparison failed on pandas dtype inference (`1` read as int
in the original-only correlation column versus float in the combined table).
It was rerun with `check_exact=True, check_dtype=False`; all values match exactly.
This was a diagnostic-check dtype issue, not a scientific-data mismatch.

Command executed: `python -m pytest tests/test_article_figures.py -k 'eof' -q`.
Result: **3 passed, 7 deselected, 0 failed**, no warnings emitted. Existing tests
cover EOF shapes/variance/unit PCs, recovery of a rank permutation and sign, and
published extreme selection. The 32 sign checks and four one-to-one checks above
were additional inline Python assertions using the pinned real data. They were
not installed as new regression tests because implementation stopped at the
user's contradiction gate. The requested 14.0239% regression is not valid.

## Downstream impact

- **Figures 9–10 and Figure 11:** both workflows derive extremes from separately
  computed total-lifecycle EOFs/PCs, not the phase EOF tables. A phase-only repair
  should not require regeneration. The comparison uses matched total PCs; the
  reproduction uses raw total PCs. Their scientific correspondence has not been
  newly validated in this phase-only audit.
- **Figure 16:** the two workflows have different definitions. Article comparison
  `fig16` shows mean LECs of positive total-PC extreme groups. Reproduction
  `render_syntheses` uses the same raw phase loadings as Figures 5–8, with
  `plot_period_means(..., 'min_max')`. Passing matched phase loadings there would
  change this figure. Decide explicitly whether it should follow published mode
  identity before regeneration; do not silently change it with shared variables.
- **EOF extreme assignments / total-lifecycle PCs:** separate data path; unchanged
  by a narrowly scoped phase matching repair. Their raw-versus-matched convention
  deserves a separate review if cross-workflow agreement is required.
- **Intense-cyclone clustering:** uses total PCs, not phase EOFs; no recomputation
  is warranted by this finding. No clustering outputs were changed.
- **Paired control:** `step6_plot_eof_diagram.py` already matches one-to-one and
  permutes variance with loadings. Its stored incipient EOF 2 also maps to raw 3
  (10.5482%, correlation 0.754484). Its paired population and inclusion of secondary
  periods differ from the article comparison (4,003 rows in later phases);
  its other phase swaps must not be substituted for the article mapping.

## Minimum next step

Confirm that the replacement Figures 5–8 should follow the existing matched
reference identities, including 10.548160122% for incipient published EOF 2.
Then reuse a shared matched phase product for both rendering paths, make raw rank
and reference identity explicit, preserve the separate raw phase-PC convention,
and add tests against the validated mapping. Review Figure 16's definition before
changing its input. Until that correction, the current Figures 5–8 set is **not
approved as a mutually consistent Correction package**. No new figures were produced.
