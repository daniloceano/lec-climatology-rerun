# Documentation

## Canonical article comparison

| Artifact | Purpose |
|---|---|
| `comparison/article_before_after_report.md` | Current report with links to every validated comparison figure |
| `article_figure_manifest.csv` | Published-to-original/corrected/comparison mapping |
| `article_artifact_dependency_audit.md` | Per-figure recomputation decision |
| `original_workflow_inventory.md` | Legacy script/input/output audit |
| `data_sources.md` | External input metadata, hashes and observed discrepancy |
| `provenance/current_to_proposed_mapping.csv` | Pre-move to final-path mapping |

The canonical comparison uses 6,789 legacy cyclones and 3,820 corrected
cyclones. Its differences combine the toolkit correction and population
change.

## Paired control

`comparison/paired_control/` contains the correction-only diagnostic report. Both sides
use the same 3,820 cyclones, so it is scientifically useful but must not be
presented as the literal article-population comparison.

## Technical records

`technical/` contains the production audit and the migration record from
`paper_energy_patterns`. These are provenance documents, not current result
reports.

The removed `lec_climatology_corrected_figures_report` represented an earlier
paired figure workflow and is retained only in Git history to prevent it from
being mistaken for the article comparison.
