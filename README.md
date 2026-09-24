# LEC climatology rerun

Reproducible recomputation and audit of the Lorenz Energy Cycle (LEC)
climatology for Southwestern Atlantic extratropical cyclones described by de
Souza et al. (2025). The production rerun uses the scientifically corrected
LorenzCycleToolKit 2.0.0 implementation.

This is a lightweight paper-oriented research repository. It stores code,
small derived tables, final figures and reports. ERA5 fields, credentials,
per-cyclone outputs and execution state remain outside Git.

## Start here

The authoritative article comparison is:

- [final PDF](docs/lec_climatology_article_before_after_report.pdf);
- [Markdown report](docs/lec_climatology_article_before_after_report.md);
- [paper figures](figures/paper/);
- [numerical results and provenance](results/article_comparison/).

It compares the complete archived article population (**6,789 legacy
cyclones; 25,000 lifecycle rows**) with the validated corrected rerun
(**3,820 cyclones; 15,829 lifecycle rows**). Differences therefore combine
the toolkit correction and the population change.

The separate [paired control](docs/paired_control/) compares the same 3,820
cyclones on both sides. Use it only to isolate the effect of the toolkit
correction. It is not the article-population comparison.

## Scientific scope

The rerun preserves the archived cyclone tracks and lifecycle windows while
recomputing the LEC with corrections to `Ca`, the fifth `Ck` subterm,
pressure-work terms, pressure-level alignment, time tendencies and NaN
handling. The production toolkit is pinned at commit
`d38cda7e37d8e8a3a937a5919640a94bef19e34a`, which contains correction commit
`d07707767c2962fed0475ff4573e7d15a97f8c69`.

Scientific definitions, assumptions, results and limitations are maintained
in [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md).

## Repository structure

```text
data/README.md                  external datasets and provenance
scripts/                        production, analysis and figure workflows
figures/paper/                  final article before/after figures (PNG + PDF)
figures/paired_control/         paired diagnostic figures
results/article_comparison/     EOFs, clusters, statistics, hashes and manifest
results/paired_control/         paired diagnostic tables
docs/                           authoritative report and documentation index
docs/paired_control/            correction-only paired report
docs/technical/                 migration and production-audit records
tests/                          focused scientific/workflow validation
```

Each major directory has its own README with ownership and regeneration
instructions.

## Environment

```bash
conda env create -f environment.yml
conda activate lec-climatology-rerun
```

The established production run is external to the repository:

```text
/p1-swell/danilocs/lec_climatology_corrected_v2
```

## Regenerate the article comparison

Run where the legacy cache, corrected cache and frozen track table are
available:

```bash
PAPER=/p1-swell/danilocs/paper_energy_patterns

python scripts/article_figures/generate_article_comparison.py \
  --legacy-cache "$PAPER/data/energy_cache.parquet" \
  --corrected-cache "$PAPER/data/corrected/energy_cache_corrected.parquet" \
  --tracks "$PAPER/data/tracks_SAt_filtered_with_energetics_processed.csv" \
  --output-root "$PWD"

python scripts/article_figures/build_article_comparison_report.py \
  --output-root "$PWD"
```

Expected products are 20 figure files (each in PNG and vector PDF), 6,789
legacy cyclones, 3,820 corrected cyclones and a 22-page consolidated report.
See [scripts/article_figures/README.md](scripts/article_figures/README.md) for
the statistical definitions and complete output inventory.

## Validate the production rerun

Heavy validation runs on `swell`:

```bash
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2

python -m scripts.lec_climatology_rerun.validate_run \
  --run-root "$RUN" --workers 8
```

The validator requires equality among the frozen population, state database
and result set, then reopens the integrated and pressure-level products. Cache
construction refuses partial state. Operational details are in
[scripts/lec_climatology_rerun/README.md](scripts/lec_climatology_rerun/README.md).

## Regenerate the paired control

```bash
PAPER=/p1-swell/danilocs/paper_energy_patterns
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2

python scripts/lec_rerun_comparison/run_all.py \
  --run-root "$RUN" \
  --legacy-cache "$PAPER/data/energy_cache.parquet" \
  --legacy-results "$PAPER/data/temp_lec_zenodo/LEC_Results_energetic-patterns" \
  --output-root "$PWD" --refresh
```

The paired workflow writes only under the clearly marked `paired_control`
directories.

## Verification

```bash
pytest -q
```

Tests focus on population selection, deterministic EOF/clustering behavior,
state recovery, validation and credential isolation. There is intentionally no
CI pipeline or packaging layer.

## Data and version-control policy

- Never commit ERA5, credentials, SQLite state, raw tracks or per-cyclone LEC
  results.
- Never overwrite archived legacy data or the validated corrected run-root.
- Version small final tables, figures, manifests, hashes and reports.
- Treat `docs/lec_climatology_article_before_after_report.pdf` as the canonical
  shareable artifact.
- Run `git pull --ff-only` before new work and review `git status` before
  committing generated products.

## Reference

de Souza et al. (2025), *Lorenz Energy Cycle Climatology for the Southwestern
Atlantic Cyclones*, *Climate Dynamics*, DOI
[10.1007/s00382-025-07918-y](https://doi.org/10.1007/s00382-025-07918-y).
