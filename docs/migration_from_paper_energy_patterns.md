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
