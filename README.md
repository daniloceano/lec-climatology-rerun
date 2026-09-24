# Corrected LEC climatology rerun

This repository preserves and operates the reproducible recomputation of the
Southwestern Atlantic cyclone Lorenz Energy Cycle (LEC) climatology published
by de Souza et al. (2025), using the scientifically corrected
LorenzCycleToolKit 2.0.0 implementation. It also generates the paired
legacy-versus-corrected comparison.

The repository is deliberately lightweight. It is a personal scientific
reproducibility and synchronization workspace, not a reusable software package
or a general service. Its priorities are explicit provenance, safe restartable
execution, validation, and documentation that remains understandable years
after the production run.

## Why the rerun exists

LorenzCycleToolKit 2.0.0 corrected equations and numerical handling that change
scientific results, including `Ca`, the fifth `Ck` subterm, `BPhi_Z`, `BPhi_E`,
vertical-level alignment, time tendencies, and NaN handling. Legacy and
corrected results are therefore preserved as distinct scientific products.

The production toolkit is pinned at commit
`d38cda7e37d8e8a3a937a5919640a94bef19e34a`, which contains correction commit
`d07707767c2962fed0475ff4573e7d15a97f8c69`.

## Authoritative population and configuration

- 3,820 cyclones with a complete ordered lifecycle and finite values for the
  seven clustering terms.
- Frozen lifecycle windows from Zenodo DOI `10.5281/zenodo.18243447`.
- Tracks from Zenodo DOI `10.5281/zenodo.18133432`.
- Exact three-hour UTC track positions.
- ERA5 pressure-level `u`, `v`, `t`, `w`, and `z`.
- Moving 15° × 15° control volume.
- 37 requested pressure levels; the toolkit analysis uses 32 levels from
  10–1000 hPa.

The scientific chain and known caveats are recorded in
[`SCIENTIFIC_NOTES.md`](SCIENTIFIC_NOTES.md).

## Repository layout

```text
scripts/lec_climatology_rerun/  preparation, scheduler, workers, monitor,
                                validation, and corrected-product builders
scripts/lec_rerun_comparison/   paired tables, statistics, figures, MD and PDF
scripts/article_figures/        corrected reconstruction of article Figures 1-16
scripts/utils/corrected_lec.py  corrected-output readers and vertical conventions
tests/                          state, validation, population and safety tests
data/README.md                  external data inventory and provenance
docs/                           historical audit, migration notes and final report
results/lec_rerun_comparison/   small final tables; large parquet caches ignored
figures/lec_rerun_comparison/   final comparison figures
figures/lec_climatology_corrected/  16 corrected figures in PNG and PDF
```

Large data and execution state live outside Git. The established production
run is:

```text
/p1-swell/danilocs/lec_climatology_corrected_v2
```

## Environment

Create the orchestration/report environment:

```bash
conda env create -f environment.yml
conda activate lec-climatology-rerun
```

The pinned LorenzCycleToolKit worktree uses the environment named by
`conda_env` in the run-root `config.json` (`lorenz` in the established run).
Credentials remain outside this repository.

## Validate the completed production

Run heavy checks on `swell`:

```bash
RUN=/p1-swell/danilocs/lec_climatology_corrected_v2

python -m scripts.lec_climatology_rerun.validate_run \
  --run-root "$RUN" --workers 8
```

`validate_run` refuses an incomplete state and checks manifest/database/result
set equality before reopening every integrated and pressure-level output.

## Build the corrected cache

The builder refuses partial state:

```bash
python -m scripts.lec_climatology_rerun.build_corrected_cache \
  --run-root "$RUN" \
  --output /p1-swell/danilocs/paper_energy_patterns/data/corrected/energy_cache_corrected.parquet
```

The output remains with the downstream article project; this repository owns
the builder, not the article's PCA, clustering, figures, or manuscript.

## Regenerate the legacy-versus-corrected comparison

```bash
PAPER=/p1-swell/danilocs/paper_energy_patterns

python scripts/lec_rerun_comparison/run_all.py \
  --run-root "$RUN" \
  --legacy-cache "$PAPER/data/energy_cache.parquet" \
  --legacy-results "$PAPER/data/temp_lec_zenodo/LEC_Results_energetic-patterns" \
  --output-root "$PWD" \
  --refresh
```

The final run must report 3,820 paired cyclones, 15,829 period rows, and no
partial/preliminary language. `corrected_phase_means.parquet` and
`paired_terms.parquet` are reproducible caches and are not committed.

The validated final products are versioned in
[`results/lec_rerun_comparison/`](results/lec_rerun_comparison/),
[`figures/lec_rerun_comparison/`](figures/lec_rerun_comparison/), and the
technical report is available as
[`Markdown`](docs/lec_rerun_comparison_report.md) or
[`PDF`](docs/lec_rerun_comparison_report.pdf).

## Recreate the article figures with corrected data

The complete figure workflow uses the legacy and validated corrected caches on
the same 3,820-cyclone population to compare all 16 main article figures:
term PDFs, phase-mean cycles, EOF cycles and track densities, the four matched
intense-cyclone groups, and the synthesis figures.

```bash
conda run -n base python scripts/article_figures/generate_comparison.py \
  --legacy-cache /p1-swell/danilocs/paper_energy_patterns/data/energy_cache.parquet \
  --corrected-cache /p1-swell/danilocs/paper_energy_patterns/data/corrected/energy_cache_corrected.parquet \
  --tracks /p1-swell/danilocs/paper_energy_patterns/data/tracks_SAt_filtered_with_energetics_processed.csv \
  --output-root "$PWD"
```

See [`scripts/article_figures/README.md`](scripts/article_figures/README.md) for
the scientific definitions, output inventory, and consolidated-report command.

## Starting a new run

Preparation requires all population-defining inputs explicitly:

```bash
python -m scripts.lec_climatology_rerun.prepare \
  --run-root /external/path/to/run \
  --population-cache /external/path/to/energy_cache.parquet \
  --track-source /external/path/to/tracks.csv \
  --periods-source /external/path/to/LEC_Results_energetic-patterns \
  --ep1-cases /external/path/to/ep1_cases.csv \
  --toolkit-source /external/path/to/LorenzCycleToolkit \
  --keys-file /external/secure/path/to/cds-keys
```

Continue with `provision`, `pilot`, `approve-production`, and `production` as
documented in
[`scripts/lec_climatology_rerun/README.md`](scripts/lec_climatology_rerun/README.md).
Never use `retry-failures`, stop a scheduler, or replace an existing run-root
without first auditing its current processes and state.

## Tests

```bash
pytest -q
```

The tests are intentionally focused on scientific population selection,
validation, state recovery, credentials isolation, and deterministic workflow
interfaces. There is no CI pipeline by design.

## Provenance and data policy

- ERA5, credentials, SQLite production state, per-cyclone results, and large
  caches are never committed.
- The run-root preserves `config.json`, `provenance.json`, the frozen manifest,
  hashes, inputs, outputs, and pinned toolkit worktree.
- Legacy outputs are never overwritten.
- Final small tables, figures, and technical reports may be versioned here as a
  reviewable record of the comparison.

See [`data/README.md`](data/README.md) for the external-data inventory and
[`docs/migration_from_paper_energy_patterns.md`](docs/migration_from_paper_energy_patterns.md)
for the repository boundary.
