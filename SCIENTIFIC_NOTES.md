# Scientific notes — corrected LEC climatology

## Scientific objective

Recompute the Lorenz Energy Cycle climatology for Southwestern Atlantic
extratropical cyclones with the corrected LorenzCycleToolKit 2.0.0 equations,
while holding the cyclone population, tracks, lifecycle windows, temporal
sampling, pressure grid, and moving-domain geometry fixed. Quantify the effect
of the correction through a paired legacy-versus-corrected analysis.

## Hypothesis and controlled comparison

The corrected implementation changes specific LEC terms and numerical
operations. The comparison is interpretable only if every other choice remains
fixed. Pairs are therefore matched by `(track_id, period)`, including secondary
periods such as `decay 2`; non-phase residual rows are excluded from phase
means.

Legacy and corrected values are not assumed to be numerically equivalent.

## Population

The authoritative population contains 3,820 cyclones selected from the legacy
phase-mean cache by these rules:

1. `incipient → intensification → mature → decay` occurs in order;
2. all seven clustering terms `Ca`, `Ck`, `BAe`, `BKe`, `Ae`, `Ke`, and `Ge`
   are finite after the workflow's aggregation;
3. lifecycle windows are frozen from the archived article results.

EP1 and other downstream article subsets are not population sources.

## Data and sampling

- Track database: Zenodo DOI `10.5281/zenodo.18133432`.
- Frozen phase windows/results: Zenodo DOI `10.5281/zenodo.18243447`.
- Atmospheric fields: ERA5 pressure-level geopotential, temperature, vertical
  velocity, and zonal/meridional wind.
- Temporal resolution: three hours, using exact UTC hours divisible by three.
- Moving computational domain: 15° × 15°, centred on the cyclone.
- Requested levels: 1–1000 hPa (37 levels).
- Actual LEC analysis levels: 10–1000 hPa (32 levels).

The manuscript statement of 100–1000 hPa conflicts with runtime and archived
outputs. This must be resolved in the manuscript, not by changing the rerun.

## Corrected terms and numerical behavior

Version 2.0.0 introduced scientifically relevant corrections including:

- baroclinic conversion `Ca`;
- the fifth `Ck` subterm;
- pressure-work boundary terms `BΦZ` and `BΦE`;
- pressure-level alignment;
- time tendencies;
- NaN handling.

The production worktree is pinned at
`d38cda7e37d8e8a3a937a5919640a94bef19e34a`, containing correction commit
`d07707767c2962fed0475ff4573e7d15a97f8c69`.

## Vertical conventions

Pressure integration is explicit and trapezoidal in pressure. The output
conventions were checked against vertically integrated toolkit values:

- no sign correction is applied to corrected `Ca`;
- `Ck` and `Ck_1…Ck_5` vertical fields are divided by `g = 9.80665` before
  pressure integration;
- `Kz` and `Ke` vertical fields are divided by `2g`;
- `Ck = Ck_1 + … + Ck_5` closes to round-off;
- `Ca = -(Ca_1 + Ca_2)` closes after its documented global sign;
- `Ce_1/Ce_2` and `Cz_1/Cz_2` are intermediates, not additive decompositions.

These rules are implemented and self-checked in
`scripts/utils/corrected_lec.py`.

## Validation invariants

A cyclone is `COMPLETE` only after validation of:

- required integrated terms and finite values;
- exact expected timestamps;
- output track equality;
- frozen lifecycle-window hash;
- all required pressure-level files, levels, timestamps, shapes, and finite
  values;
- toolkit completion marker.

The corrected cache must never be built from a partial population.

## Completed production record

The established run-root is
`/p1-swell/danilocs/lec_climatology_corrected_v2`. On 2026-09-09 it reached
3,820/3,820 `COMPLETE`, with no pending, active, retryable, or final failures.
An independent reopening of all 3,820 outputs produced zero validation errors.

The final phase-mean cache contains 15,829 period rows for 3,820 cyclones.
Secondary lifecycle periods explain why this is not simply `3,820 × 4`.

## Interpretation boundaries

This repository establishes and compares the corrected climatology. It does
not update PCA, k-means clusters, Energy Pattern labels, principal manuscript
figures, or manuscript conclusions. Those are downstream responsibilities of
`paper_energy_patterns`.

## Caveats

- CDS failures are operational and may exhaust retry limits even when the
  scientific configuration is valid.
- The run-root is large and server-only; repository clones contain code and
  small final products, not the production state.
- Higher EOF modes may swap order because their explained variances are close;
  corrected modes are matched to legacy modes by absolute pattern correlation.
