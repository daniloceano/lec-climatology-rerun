# Scientific notes - corrected LEC climatology

## Research Questions

1. How does the Southwestern Atlantic cyclone LEC climatology change after
   applying the LorenzCycleToolKit 2.0.0 scientific corrections?
2. Which differences arise from the correction itself, and which also reflect
   the smaller validated rerun population?
3. How do the corrected phase cycles, EOF patterns, track-density extremes and
   intense-cyclone groups compare with the published article?

## Physical / Statistical Framework

The Lorenz Energy Cycle is represented by the reservoirs $A_Z$, $A_E$, $K_Z$
and $K_E$, their conversions $C_Z$, $C_A$, $C_K$ and $C_E$, generation,
boundary transports and budget tendencies. Energy reservoirs are vertically
integrated in J m$^{-2}$; conversions, generation, transports and tendencies
are expressed in W m$^{-2}$.

Pressure integration is trapezoidal in pressure. The checked corrected-output
conventions are:

- no additional sign correction for corrected $C_A$;
- $C_K$ and $C_{K1}\ldots C_{K5}$ divided by $g=9.80665$ before integration;
- $K_Z$ and $K_E$ divided by $2g$;
- $C_K=\sum_{i=1}^{5}C_{Ki}$ closes to round-off;
- $C_A=-(C_{A1}+C_{A2})$ closes after the documented global sign;
- $C_{E1}/C_{E2}$ and $C_{Z1}/C_{Z2}$ are intermediates, not additive
  decompositions.

## Datasets and Variables

- Cyclone tracks: Zenodo DOI `10.5281/zenodo.18133432`, 1979-2020.
- Archived article LEC results and lifecycle windows: Zenodo DOI
  `10.5281/zenodo.18243447`.
- ERA5 pressure-level `u`, `v`, `t`, `w` and `z`, sampled every three hours.
- Moving 15 degree by 15 degree control volume centred on each cyclone.
- 37 requested pressure levels; the toolkit analysis uses 32 levels from
  10-1000 hPa.
- Published archive: 6,789 cyclones and 25,000 lifecycle rows.
- Validated corrected cache: 3,820 cyclones and 15,829 lifecycle rows.

The manuscript statement of 100-1000 hPa conflicts with runtime and archived
outputs. This remains a manuscript caveat; the rerun follows the verified
10-1000 hPa implementation.

## Methodology

### Corrected production rerun

The authoritative population contains 3,820 cyclones with an ordered
`incipient -> intensification -> mature -> decay` lifecycle and finite values
for the population-defining LEC terms. Lifecycle windows are frozen from the
archive. A cyclone becomes `COMPLETE` only after checking timestamps, track
equality, lifecycle-window hash, integrated terms, required pressure-level
files, dimensions and finite values.

The production worktree is pinned at
`d38cda7e37d8e8a3a937a5919640a94bef19e34a`, including correction commit
`d07707767c2962fed0475ff4573e7d15a97f8c69`.

### Article-population before/after comparison

The authoritative report compares two independent populations:

- **before:** all 6,789 archived legacy cyclones and all 25,000 archived
  lifecycle rows;
- **after:** all 3,820 validated corrected cyclones and all 15,829 corrected
  lifecycle rows.

Primary phase panels retain exact `period == phase` records: 22,464 legacy and
15,280 corrected rows. Total-lifecycle EOFs first average every archived period
by cyclone and then use the correlation matrix of the 24 published LEC terms.
EOFs are fitted independently. Corrected modes are matched one-to-one to
legacy modes by maximum absolute loading-pattern correlation and sign-aligned.

PC extremes are screened against the upper and lower deciles of PCs 1-8. Each
cyclone is assigned to its dominant extreme, after which Figures 9-11 and 16
retain dominant EOFs 1-4. Figure 16 shows the mean LEC of the positive EOF
cyclone groups, not an EOF-loading diagram.

Intense cyclones satisfy the pointwise 90th-percentile vorticity criterion.
Five K-means groups are fitted independently to the first eight aligned
total-lifecycle PC scores. The corrected centroids are matched to the legacy
centroids for comparison.

### Paired correction-only control

The paired control restricts both sides to the same 3,820 cyclones and matched
`(track_id, period)` rows. It isolates equation and numerical corrections while
holding population and lifecycle windows fixed. It is a diagnostic control,
not a reproduction of the full article population.

## Assumptions

- Archived legacy phase means faithfully represent the article calculation;
  direct checks against per-cyclone archive CSVs agree to numerical round-off.
- The frozen track database supplies the spatial and intensity metadata for
  both versions.
- EOF sign is arbitrary; sign alignment does not alter the represented mode.
- Centroid matching makes cluster labels comparable but does not imply that
  clusters are identical physical populations.
- Secondary lifecycle periods enter total-lifecycle analyses but not the exact
  four-primary-phase panels.

## Results and Interpretation

### 2026-09-24 - article comparison reconstruction

The archived total-lifecycle calculation reproduces the article EOF 1-4
variance fractions: **28.304%, 11.018%, 10.925% and 8.188%**. This numerical
landmark verifies the full 6,789-cyclone legacy input definition.

The intense-cyclone PC analysis contains 1,744 legacy and 1,486 corrected
systems. The final comparison comprises 20 files for article Figures 1-16,
including split Figures 12 and 16.

Interpretation must distinguish the two comparisons. The article-population
report answers how the published result changes after the validated rerun, but
its differences combine correction and population. The paired control is the
appropriate source for statements attributable only to the toolkit correction.

## Caveats and Limitations

- The corrected production covers 3,820 of the 6,789 archived article
  cyclones; a complete corrected 6,789-cyclone population would require a new
  ERA5 acquisition and rerun.
- Higher EOF modes can exchange rank because their explained variances are
  close; the report uses pattern matching rather than assuming rank stability.
- LEC distributions are heavy-tailed. Means, medians, standard deviations and
  display trimming must not be interpreted interchangeably.
- The repository contains derived products, not the server-side ERA5 or full
  per-cyclone run-root.

## Next Steps

1. Interpret the scientific changes figure by figure, explicitly separating
   article-population changes from paired correction effects.
2. Update manuscript text and tables using the canonical report and numerical
   result files.
3. Decide whether a full 6,789-cyclone corrected rerun is scientifically worth
   the ERA5 download and computational cost.

## References

- de Souza et al. (2025), *Lorenz Energy Cycle Climatology for the
  Southwestern Atlantic Cyclones*, *Climate Dynamics*, DOI
  `10.1007/s00382-025-07918-y`.
- Cyclone tracks: Zenodo DOI `10.5281/zenodo.18133432`.
- Archived LEC results: Zenodo DOI `10.5281/zenodo.18243447`.
