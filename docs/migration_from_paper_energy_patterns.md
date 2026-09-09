# Migration boundary from `paper_energy_patterns`

## Purpose

This repository owns the operational rerun of the corrected LEC climatology
and the legacy-versus-corrected comparison. The article repository consumes
corrected derived products but no longer orchestrates their production.

## Migrated components

- `scripts/lec_climatology_rerun/`
- `scripts/lec_rerun_comparison/`
- run-root readers and vertical conventions needed by the builders
- rerun tests and validation
- operational and scientific documentation
- final comparison report, small tables, and figures

## Components remaining in the article repository

- the legacy cache and archived inputs used by the paper;
- the corrected cache consumed by downstream PCA/k-means;
- a small corrected-product metadata interface used by Ck-subterm analyses;
- article-specific PCA, clustering, Energy Patterns, figures, results, and
  manuscript text;
- legacy results required to reproduce the paper and serve as the comparison's
  explicit “before” side.

## External interfaces

The new repository does not assume that legacy inputs live below its own
`data/` directory. `run_all.py` accepts:

- `--run-root`;
- `--legacy-cache`;
- `--legacy-results`;
- `--output-root`.

Equivalent environment variables are `LEC_RERUN_ROOT`, `LEC_CORRECTED_DATA`,
`LEC_LEGACY_CACHE`, `LEC_LEGACY_RESULTS`, and
`LEC_COMPARISON_OUTPUT_ROOT`.

## Equivalence requirement

Before deleting the original implementations, the migrated workflow must:

1. validate the established run-root;
2. regenerate the comparison from the same legacy inputs;
3. reproduce numerical tables exactly;
4. reproduce deterministic figures by hash where possible;
5. distinguish PDF timestamps/rendering metadata from scientific differences.

No numerical difference is accepted silently.

## Executed cutover validation

The migration was validated on `swell` on 2026-09-09 before the original
implementation was retired:

- the production database contained exactly 3,820 `COMPLETE` rows and no
  other state;
- manifest, database, and result-directory ID sets were identical;
- all 3,820 integrated and pressure-level outputs were reopened with zero
  validation errors;
- the corrected cache contained 15,829 lifecycle-period rows for all 3,820
  cyclones (SHA-256
  `c5efb8242e83aaa85ebd39cc12d5630fc0f70608775a67d32821dc0097d8d4d3`);
- the migrated comparison reproduced 3,820 paired cyclones, 15,829 paired
  period rows, and 379,896 paired term values;
- all scientific CSV/Parquet tables were byte-for-byte or value/dtype/order
  identical to the pre-migration products;
- all 12 PNG figures and the Markdown report were byte-for-byte identical;
- the 12 figure PDFs and nine-page report PDF rendered pixel-identically.

The binary PDF hashes differ only because the PDF generators embed creation
metadata. No scientific or visible difference was found.
